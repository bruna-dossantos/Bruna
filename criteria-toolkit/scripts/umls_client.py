#!/usr/bin/env python3
"""
umls_client.py

Look up clinical terms in the UMLS UTS REST API and return authoritative
definitions from NLM — used to gloss clinical terms inside a policy.

Auth (modern flow — no TGT/ticket dance):
  Every request just appends ?apiKey=<key> against https://uts-ws.nlm.nih.gov/rest
  The key is read from, in order:
    1. --api-key on the command line
    2. env var UMLS_API_KEY
    3. ~/Claude/Projects/Credentials/umls_api_key.txt

Get a key: sign in at https://uts.nlm.nih.gov -> profile -> "Generate API Key".

Commands:
  # single term -> best definition
  python3 umls_client.py define "obstructive sleep apnea"

  # a list of terms (one per line) -> a markdown glossary
  python3 umls_client.py glossary terms.txt

  # annotate a policy: gloss each term the first time it appears, footnote style
  python3 umls_client.py annotate policy.md terms.txt > policy.glossed.md

Import as a library:
  from umls_client import UMLSClient
  c = UMLSClient()
  print(c.define("hypercapnia"))
"""

import os
import re
import sys
import html
import json
import argparse
from pathlib import Path

import requests

BASE = "https://uts-ws.nlm.nih.gov/rest"
KEY_FILE = Path.home() / "Claude/Projects/Credentials/umls_api_key.txt"

# Optional user-editable overrides, loaded if present (merged over built-ins).
# Shape: {"synonyms": {"term": ["alt lookup", ...]}, "manual": {"term": "gloss"}}
SYNONYM_FILE = Path(__file__).with_name("umls_synonyms.json")

# When a term in a policy has no useful UMLS concept/definition, look up these
# clinically-equivalent phrasings instead. Keys are lowercased; first synonym
# that yields a real definition wins. Grow this via umls_synonyms.json.
SYNONYMS = {
    "symptomatology": ["symptom"],
    "symptoms": ["symptom"],
    "focal problem": ["focal neurologic sign", "neurological deficit"],
    "focal deficit": ["focal neurologic sign", "neurological deficit"],
    "focal neurological deficit": ["focal neurologic sign", "neurological deficit"],
    "bleeding": ["hemorrhage"],
    "intracranial bleeding": ["intracranial hemorrhage"],
    "tumor": ["neoplasm"],
    "mass": ["neoplasm"],
    "aneurysm": ["intracranial aneurysm"],
    "ct": ["computed tomography"],
    "ct scan": ["computed tomography"],
    "mri": ["magnetic resonance imaging"],
    "avm": ["arteriovenous malformation"],
    "stroke": ["cerebrovascular accident"],
    "tia": ["transient ischemic attack"],
}

# Last-resort plain-language glosses for concepts UMLS carries but never defines.
# Marked as source "manual" in output so they're visibly not from NLM.
MANUAL_GLOSS = {
    "focal problem": (
        "A neurological finding localized to one specific area of the nervous "
        "system (e.g. one-sided weakness or a visual field cut), pointing to a "
        "discrete lesion rather than a diffuse cause."
    ),
    "focal neurological deficit": (
        "A neurological finding localized to one specific area of the nervous "
        "system (e.g. one-sided weakness or a visual field cut), pointing to a "
        "discrete lesion rather than a diffuse cause."
    ),
}


def _load_overrides():
    """Merge umls_synonyms.json (if present) over the built-in maps."""
    syn = {k.lower(): v for k, v in SYNONYMS.items()}
    man = {k.lower(): v for k, v in MANUAL_GLOSS.items()}
    if SYNONYM_FILE.exists():
        try:
            data = json.loads(SYNONYM_FILE.read_text())
        except json.JSONDecodeError as e:
            print(f"WARNING: could not parse {SYNONYM_FILE.name}: {e}", file=sys.stderr)
            data = {}
        for k, v in (data.get("synonyms") or {}).items():
            syn[k.lower()] = v if isinstance(v, list) else [v]
        for k, v in (data.get("manual") or {}).items():
            man[k.lower()] = v
    return syn, man

# Definition sources, best-first. UMLS returns definitions from many vocabularies;
# these tend to be the most clinically useful for glossing.
SOURCE_PREFERENCE = [
    "NCI",    # NCI Thesaurus — clean, plain-language clinical definitions
    "MSH",    # MeSH
    "CSP",    # CRISP Thesaurus
    "HPO",    # Human Phenotype Ontology
    "MDR",    # MedDRA
    "NANDA-I",
    "PDQ",
    "AIR",
    "ICF",
    "MEDLINEPLUS",
]

# Plain-language / consumer-health ordering — MedlinePlus first. Use for glossing
# a policy for non-clinical readers.
PLAIN_PREFERENCE = ["MEDLINEPLUS", "NCI", "CSP", "MSH", "HPO"]

# English-language source allowlist. Anything else (e.g. MSHCZE, MSHSPA, MSHNOR)
# is only used as a last resort when no English definition exists.
ENGLISH_SOURCES = set(SOURCE_PREFERENCE) | {"CHV", "AIR", "SNOMEDCT_US"}


class UMLSError(RuntimeError):
    pass


class UMLSClient:
    def __init__(self, api_key: str | None = None, version: str = "current"):
        self.api_key = api_key or self._resolve_key()
        if not self.api_key:
            raise UMLSError(
                "No UMLS API key found. Pass --api-key, set UMLS_API_KEY, "
                f"or write the key to {KEY_FILE}"
            )
        self.version = version
        self.session = requests.Session()
        self.synonyms, self.manual_gloss = _load_overrides()

    @staticmethod
    def _resolve_key() -> str | None:
        env = os.environ.get("UMLS_API_KEY")
        if env:
            return env.strip()
        if KEY_FILE.exists():
            return KEY_FILE.read_text().strip()
        return None

    def _get(self, path: str, **params):
        params["apiKey"] = self.api_key
        r = self.session.get(f"{BASE}{path}", params=params, timeout=30)
        if r.status_code == 401:
            raise UMLSError("401 Unauthorized — the API key was rejected.")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def search(self, term: str, search_type: str = "words", sabs: str | None = None):
        """Return a list of {ui (CUI), name, rootSource} for a term, best match first."""
        params = {"string": term, "searchType": search_type, "pageSize": 10}
        if sabs:
            params["sabs"] = sabs
        data = self._get(f"/search/{self.version}", **params)
        if not data:
            return []
        results = data.get("result", {}).get("results", [])
        return [r for r in results if r.get("ui") and r["ui"] != "NONE"]

    def definitions(self, cui: str):
        """Return a list of {source, value} definitions for a CUI."""
        data = self._get(f"/content/{self.version}/CUI/{cui}/definitions")
        if not data:
            return []
        out = []
        for d in data.get("result", []):
            out.append({
                "source": d.get("rootSource", ""),
                "value": _clean(d.get("value", "")),
            })
        return out

    def atoms(self, cui: str, language: str = "ENG", max_pages: int = 4,
              include_suppressible: bool = False):
        """
        All atoms (synonymous strings across source vocabularies) for a CUI.
        Atoms are the authoritative synonym set for one concept — the right
        recall source for an extraction field, and they also carry real source
        codes (e.g. ICD-10-CM) for the exact concept, with no fuzzy-search noise.
        Filters obsolete/suppressible atoms by default.
        """
        out = []
        for pg in range(1, max_pages + 1):
            data = self._get(f"/content/{self.version}/CUI/{cui}/atoms",
                             language=language, pageSize=100, pageNumber=pg)
            if not data:
                break
            res = data.get("result", [])
            if not res:
                break
            for a in res:
                if not include_suppressible and (_truthy(a.get("suppressible"))
                                                 or _truthy(a.get("obsolete"))):
                    continue
                out.append(a)
            if len(res) < 100:
                break
        return out

    def best_definition(self, cui: str, plain: bool = False) -> dict | None:
        defs = self.definitions(cui)
        if not defs:
            return None
        # Prefer English sources; only fall back to non-English if that's all there is.
        english = [d for d in defs if d["source"] in ENGLISH_SOURCES]
        pool = english or defs
        pref = PLAIN_PREFERENCE if plain else SOURCE_PREFERENCE
        rank = {s: i for i, s in enumerate(pref)}
        pool.sort(key=lambda d: rank.get(d["source"], len(pref)))
        return pool[0]

    def define(self, term: str, plain: bool = False) -> dict:
        """
        Resolve a term to a concept and its best definition, trying synonyms and
        finally a manual gloss when UMLS has no definition text.

        Returns {term, cui, name, source, definition, resolved_via}:
          - resolved_via is the lookup string that produced the definition
            (differs from `term` when a synonym was used).
          - source == "manual" means the definition came from MANUAL_GLOSS,
            not from NLM.
          - definition is None only when nothing resolved at all.
        """
        # Try the original term first, then any configured synonyms, keeping the
        # first concept we find as a fallback even if it lacks a definition.
        candidates = [term] + self.synonyms.get(term.lower().strip(), [])
        fallback = None
        for cand in candidates:
            hits = self.search(cand)
            if not hits:
                continue
            top = hits[0]
            cui = top["ui"]
            best = self.best_definition(cui, plain=plain)
            if best:
                return {
                    "term": term, "cui": cui, "name": top.get("name"),
                    "source": best["source"], "definition": best["value"],
                    "resolved_via": None if cand == term else cand,
                }
            if fallback is None:
                fallback = {"term": term, "cui": cui, "name": top.get("name"),
                            "source": None, "definition": None, "resolved_via":
                            None if cand == term else cand}

        # No UMLS definition anywhere — try a manual gloss.
        manual = self.manual_gloss.get(term.lower().strip())
        if manual:
            base = fallback or {"term": term, "cui": None, "name": None,
                                "resolved_via": None}
            return {**base, "source": "manual", "definition": manual}

        return fallback or {"term": term, "cui": None, "name": None,
                            "source": None, "definition": None, "resolved_via": None}


def _truthy(v):
    return v is True or (isinstance(v, str) and v.strip().lower() == "true")


def _clean(text: str) -> str:
    """UMLS definition values sometimes carry HTML/entities and stray whitespace."""
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _read_terms(path: str) -> list[str]:
    lines = Path(path).read_text().splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def cmd_define(client: UMLSClient, args):
    res = client.define(args.term, plain=args.plain)
    if not res["cui"]:
        print(f"No UMLS concept found for: {args.term}")
        return
    via = f"  [via synonym: {res['resolved_via']}]" if res.get("resolved_via") else ""
    print(f"{res['term']}  ->  {res['name']}  (CUI {res['cui']}){via}")
    if res["definition"]:
        tag = "MANUAL" if res["source"] == "manual" else res["source"]
        print(f"[{tag}] {res['definition']}")
    else:
        print("(concept found, but no textual definition in UMLS)")


def cmd_glossary(client: UMLSClient, args):
    terms = _read_terms(args.terms_file)
    print("## Clinical terms glossary\n")
    for t in terms:
        res = client.define(t, plain=args.plain)
        if res["definition"]:
            if res["source"] == "manual":
                src = "manual gloss — not from UMLS"
            else:
                via = f", via {res['resolved_via']}" if res.get("resolved_via") else ""
                src = f"UMLS {res['cui']}, source {res['source']}{via}"
            print(f"- **{t}** — {res['definition']} _({src})_")
        elif res["cui"]:
            print(f"- **{t}** — _(concept {res['cui']}; no UMLS definition — "
                  f"needs a manual gloss)_")
        else:
            print(f"- **{t}** — _(no UMLS match — check spelling / phrasing)_")


def cmd_annotate(client: UMLSClient, args):
    text = Path(args.policy_file).read_text()
    terms = _read_terms(args.terms_file)
    notes = []
    for i, t in enumerate(terms, 1):
        res = client.define(t, plain=args.plain)
        gloss = res["definition"] or "(no UMLS definition found)"
        # footnote the first whole-word, case-insensitive occurrence only
        pat = re.compile(rf"\b({re.escape(t)})\b", re.IGNORECASE)
        text, n = pat.subn(rf"\1[^{i}]", text, count=1)
        if n:
            src = f" (UMLS {res['cui']}/{res['source']})" if res["cui"] else ""
            notes.append(f"[^{i}]: **{t}** — {gloss}{src}")
    print(text)
    if notes:
        print("\n---\n")
        print("\n".join(notes))


def main(argv=None):
    # shared flags usable either before or after the subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--api-key", help="UMLS API key (else env/creds file)")
    common.add_argument("--plain", action="store_true",
                        help="prefer plain-language (MedlinePlus) definitions for lay readers")

    p = argparse.ArgumentParser(description="UMLS UTS clinical-term lookup", parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("define", help="look up one term", parents=[common])
    d.add_argument("term")

    g = sub.add_parser("glossary", help="glossary from a term list file", parents=[common])
    g.add_argument("terms_file")

    a = sub.add_parser("annotate", help="footnote-gloss terms inside a policy", parents=[common])
    a.add_argument("policy_file")
    a.add_argument("terms_file")

    args = p.parse_args(argv)
    client = UMLSClient(api_key=args.api_key)

    {"define": cmd_define, "glossary": cmd_glossary, "annotate": cmd_annotate}[args.cmd](client, args)


if __name__ == "__main__":
    try:
        main()
    except UMLSError as e:
        sys.exit(f"ERROR: {e}")
