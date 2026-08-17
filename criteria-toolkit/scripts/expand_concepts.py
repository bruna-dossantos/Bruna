#!/usr/bin/env python3
"""
expand_concepts.py  —  Way 1: LLM-propose -> ontology-validate -> harness-gate

The high-quality expansion path. A script cannot invent good clinical synonyms
(raw ontology search underdelivers — see the recall demo), but the MODEL can.
So the division of labor is:

  1. The model (you, the agent, or any LLM) PROPOSES candidate expansions for a
     seed term — the common clinical realizations a policy means.
  2. THIS COMMAND validates each candidate against BioPortal/UMLS: keeps only the
     ones that resolve to a real ontology concept, attaches the grounded label,
     UMLS CUI, and ICD-10-CM candidates, and drops (flags) anything that doesn't
     resolve — the hallucination guardrail.
  3. Optionally, `test` gates the resulting concept_set on recall/precision
     against real chart snippets before it ships into an extraction field.

Ontology as validator, not generator.

Usage:
  # validate model-proposed candidates -> grounded concept_set JSON
  python3 expand_concepts.py validate \
      --seed "spinal infection" \
      --candidates "spondylodiscitis,discitis,vertebral osteomyelitis,epidural abscess" \
      --out spinal_infection.concept_set.json

  # candidates can also come from a file (one per line) or stdin
  python3 expand_concepts.py validate --seed "spinal infection" --candidates-file cands.txt

  # gate a concept_set on recall/precision
  #   charts.tsv: each line = "1<TAB>chart text"  (1 = truly positive, 0 = negative)
  python3 expand_concepts.py test --concept-set spinal_infection.concept_set.json --charts charts.tsv
"""

import os
import re
import sys
import json
import argparse
import urllib.parse
from pathlib import Path

# Import the BioPortal client sitting next to this file (auth + session reuse).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bioportal_client import BioPortalClient, BASE  # noqa: E402

try:
    from umls_client import UMLSClient
    _HAS_UMLS = True
except Exception:
    _HAS_UMLS = False

GROUND_ONTOLOGIES = "SNOMEDCT,NCIT"

# Generic head-words that alone don't make a match meaningful. If a term's only
# overlap with a candidate label is one of these, it isn't really grounded.
_GENERIC = {
    "syndrome", "disease", "disorder", "condition", "finding", "nos", "other",
    "unspecified", "of", "the", "and", "or", "with", "due", "to", "caused", "by",
    "in", "a", "an", "acquired", "congenital", "chronic", "acute",
}


_ICD_RE = re.compile(r"^[A-TV-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?$")


def _clean_atom(name):
    """Normalize a UMLS atom string for use as a recall term; drop index-inversion
    junk (e.g. 'head; pain', 'Pain, Head') that never matches real chart prose."""
    n = name or ""
    if ";" in n:                       # 'head; pain', 'blood; extravasation'
        return ""
    if re.search(r"\w,\s*\w", n):      # comma inversions: 'Pain, Head'
        # keep qualifier commas ('Headache, unspecified'); drop word-word inversions
        head, _, tail = n.partition(",")
        if tail.strip().lower() not in ("unspecified", "nos") and " " not in head.strip():
            return ""
    n = re.sub(r"\s*\([^)]*\)\s*$", "", n)   # trailing "(finding)" etc.
    n = re.sub(r",?\s*NOS$", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip()


def _tokens(s):
    return [w for w in re.findall(r"[a-z0-9]+", (s or "").lower())]


def _label_supports(term, label):
    """
    True if `label` plausibly grounds `term`: the most distinctive (longest
    non-generic) token of the term must appear in the label. Rejects fuzzy
    matches whose only shared token is generic ('floogle syndrome' -> 'Syndrome').
    """
    qt = [t for t in _tokens(term) if t not in _GENERIC] or _tokens(term)
    if not qt:
        return False
    lab = set(_tokens(label))
    distinctive = max(qt, key=len)
    return distinctive in lab


class ConceptExpander:
    def __init__(self):
        self.bp = BioPortalClient()
        self.umls = UMLSClient() if _HAS_UMLS and _umls_key_present() else None
        self._atoms_cache = {}

    def _bp_search(self, term, ontologies, pagesize=5):
        r = self.bp.session.get(f"{BASE}/search", params={
            "q": term, "ontologies": ontologies, "pagesize": pagesize,
            "include": "prefLabel",
        }, timeout=60)
        r.raise_for_status()
        return r.json().get("collection", [])

    def icd10_candidates(self, term, limit=6):
        """Fuzzy ICD-10-CM hits, filtered so the code's label supports the term.
        These are always review-tier candidates, never authoritative."""
        out = []
        for h in self._bp_search(term, "ICD10CM", pagesize=12):
            if _label_supports(term, h.get("prefLabel") or ""):
                out.append({"code": h["@id"].split("/")[-1], "label": h.get("prefLabel")})
            if len(out) >= limit:
                break
        return out

    def ground(self, term):
        """
        Resolve one term to a real ontology concept. Fuzzy search, but only accept
        a hit whose label actually SUPPORTS the term (shares its distinctive token)
        — this is the hallucination guardrail: 'floogle syndrome' fuzzy-matches
        'Syndrome' but fails the token check, so it does not resolve.
        """
        rec = {"term": term, "resolved": False, "resolved_label": None,
               "ontology": None, "cui": None, "icd10": []}
        for h in self._bp_search(term, GROUND_ONTOLOGIES, pagesize=5):
            label = h.get("prefLabel") or ""
            if _label_supports(term, label):
                rec.update(resolved=True, resolved_label=label,
                           ontology=h["links"]["ontology"].split("/")[-1])
                break
        if rec["resolved"]:
            rec["icd10"] = self.icd10_candidates(term)
            if self.umls:
                try:
                    u = self.umls.search(term)
                    rec["cui"] = u[0]["ui"] if u else None
                except Exception:
                    pass
        return rec

    def atoms_concept_set(self, seed):
        """
        Build a concept set from UMLS ATOMS — the authoritative synonym strings for
        the seed's concept (same CUI), plus ICD-10-CM codes taken straight from the
        concept's ICD atoms (no fuzzy-search noise). This is the preferred recall
        source for an extraction field: precise synonyms, not the model's guess at
        related conditions.
        """
        if not self.umls:
            raise RuntimeError("UMLS key required for atoms-based expansion "
                               "(set UMLS_API_KEY or the creds file).")
        ck = seed.strip().lower()
        if ck in self._atoms_cache:
            return self._atoms_cache[ck]
        hits = self.umls.search(seed)
        if not hits:
            miss = {"seed": seed, "cui": None, "name": None, "match_terms": [seed],
                    "icd10_candidates": [], "icd_source": None, "atom_count": 0}
            self._atoms_cache[ck] = miss
            return miss
        cui, name = hits[0]["ui"], hits[0].get("name")
        atoms = self.umls.atoms(cui)
        names, icd = [], set()
        for a in atoms:
            nm = _clean_atom(a.get("name", ""))
            if nm and len(nm) > 3 and nm.lower() not in {x.lower() for x in names}:
                names.append(nm)
            if a.get("rootSource") in ("ICD10CM", "ICD10"):
                code = (a.get("code") or "").rstrip("/").split("/")[-1]
                if _ICD_RE.match(code):
                    icd.add(code)
        icd_source = "umls_atoms"
        # Some concepts' CUIs carry no ICD atom — fall back to the guarded
        # BioPortal ICD search so the field still gets candidate codes to review.
        if not icd:
            try:
                icd = {c["code"] for c in self.icd10_candidates(name or seed)}
                icd_source = "bioportal_fuzzy_review"
            except Exception:
                pass
        match_terms = []
        for t in [seed, name] + names:
            if t and t.lower() not in {m.lower() for m in match_terms}:
                match_terms.append(t)
        # definition for the concept (enrichment): prefer clinical NCI-style text
        definition, def_source = None, None
        try:
            best = self.umls.best_definition(cui)
            if best:
                definition, def_source = best["value"], best["source"]
        except Exception:
            pass
        result = {"seed": seed, "cui": cui, "name": name,
                  "match_terms": match_terms, "icd10_candidates": sorted(icd),
                  "icd_source": icd_source, "atom_count": len(atoms),
                  "definition": definition, "definition_source": def_source}
        self._atoms_cache[ck] = result
        return result

    def validate(self, seed, candidates):
        """
        Ground the seed + every model-proposed candidate.

        Two different risk profiles, handled differently:
          - match_terms (the recall list an extraction field searches on): INCLUSIVE.
            Every model candidate stays, in the MODEL'S surface phrasing — a bogus
            term matches no real chart (harmless), a missing real term is a recall
            loss (harmful). We never inject the ontology's broadened label (that is
            what made 'vertebral osteomyelitis' match a wrist 'osteomyelitis' chart).
          - ICD-10 candidates: GUARDED. A wrong diagnosis code is harmful, so codes
            come only from terms that ground to a real concept, label-token checked.
          - unverified: terms the ontology could not confirm. Kept in match_terms
            but flagged so a human checks for a typo/hallucination before shipping.
        """
        uniq, seen = [], set()
        for t in [seed] + [c for c in candidates if c.strip()]:
            k = t.strip().lower()
            if k and k not in seen:
                seen.add(k)
                uniq.append(t.strip())
        grounded = [self.ground(t) for t in uniq]
        unverified = [g["term"] for g in grounded
                      if not g["resolved"] and g["term"].lower() != seed.lower()]
        match_terms = [g["term"] for g in grounded]  # inclusive, model phrasing
        icd10 = sorted({c["code"] for g in grounded if g["resolved"]
                        for c in g["icd10"]})
        return {
            "seed": seed,
            "grounded": grounded,
            "match_terms": match_terms,
            "unverified": unverified,
            "icd10_candidates": icd10,
            "needs_review": bool(unverified),
        }


def _umls_key_present():
    return bool(os.environ.get("UMLS_API_KEY")) or \
        (Path.home() / "Claude/Projects/Credentials/umls_api_key.txt").exists()


# ---- recall/precision harness (Way 1 step 3) --------------------------------

def _extract_hit(text, terms):
    t = text.lower()
    for term in terms:
        if term and re.search(rf"\b{re.escape(term.lower())}\b", t):
            return term
    return None


def run_test(concept_set, charts):
    terms = concept_set["match_terms"]
    tp = fn = fp = tn = 0
    misses, false_hits = [], []
    for truth, text in charts:
        hit = _extract_hit(text, terms)
        if truth and hit:
            tp += 1
        elif truth and not hit:
            fn += 1; misses.append(text)
        elif not truth and hit:
            fp += 1; false_hits.append((text, hit))
        else:
            tn += 1
    pos = tp + fn
    return {
        "recall": tp / pos if pos else None,
        "true_positives": tp, "false_negatives": fn,
        "false_positives": fp, "true_negatives": tn,
        "misses": misses, "false_hits": false_hits,
    }


# ---- CLI --------------------------------------------------------------------

def _load_candidates(args):
    if args.candidates:
        return [c.strip() for c in args.candidates.split(",") if c.strip()]
    if args.candidates_file:
        return [ln.strip() for ln in Path(args.candidates_file).read_text().splitlines()
                if ln.strip() and not ln.startswith("#")]
    # stdin
    if not sys.stdin.isatty():
        return [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]
    return []


def cmd_validate(args):
    exp = ConceptExpander()
    candidates = _load_candidates(args)
    result = exp.validate(args.seed, candidates)
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    print(text)
    g = sum(1 for x in result["grounded"] if x["resolved"])
    print(f"\n# {len(result['match_terms'])} recall terms | {g} ontology-grounded | "
          f"{len(result['icd10_candidates'])} ICD-10 candidates", file=sys.stderr)
    if result["unverified"]:
        print(f"# UNVERIFIED (kept for recall, review for typo/hallucination): "
              f"{', '.join(result['unverified'])}", file=sys.stderr)


def cmd_atoms(args):
    exp = ConceptExpander()
    res = exp.atoms_concept_set(args.seed)
    text = json.dumps(res, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    print(text)
    print(f"\n# CUI {res['cui']} ({res['name']}): {len(res['match_terms'])} synonym terms, "
          f"{len(res['icd10_candidates'])} ICD-10 codes from {res['atom_count']} atoms",
          file=sys.stderr)


def cmd_test(args):
    concept_set = json.loads(Path(args.concept_set).read_text())
    charts = []
    for ln in Path(args.charts).read_text().splitlines():
        if not ln.strip():
            continue
        label, _, text = ln.partition("\t")
        charts.append((label.strip() == "1", text.strip()))
    res = run_test(concept_set, charts)
    print(f"seed: {concept_set['seed']}   terms: {len(concept_set['match_terms'])}")
    r = res["recall"]
    print(f"recall = {res['true_positives']}/{res['true_positives']+res['false_negatives']} "
          f"= {r:.0%}" if r is not None else "recall = n/a")
    print(f"false positives = {res['false_positives']}")
    for m in res["misses"]:
        print(f"  MISS: {m}")
    for txt, term in res["false_hits"]:
        print(f"  FALSE POSITIVE (matched '{term}'): {txt}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Validate model-proposed concept expansions against ontologies")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="ground candidate expansions -> concept_set")
    v.add_argument("--seed", required=True)
    v.add_argument("--candidates", help="comma-separated candidate terms")
    v.add_argument("--candidates-file", help="file with one candidate per line")
    v.add_argument("--out", help="write concept_set JSON here")

    a = sub.add_parser("atoms", help="build a concept_set from UMLS atoms (synonyms + ICD)")
    a.add_argument("--seed", required=True)
    a.add_argument("--out", help="write concept_set JSON here")

    t = sub.add_parser("test", help="gate a concept_set on recall/precision")
    t.add_argument("--concept-set", required=True)
    t.add_argument("--charts", required=True, help="TSV: '1|0<TAB>chart text' per line")

    args = p.parse_args(argv)
    {"validate": cmd_validate, "atoms": cmd_atoms, "test": cmd_test}[args.cmd](args)


if __name__ == "__main__":
    main()
