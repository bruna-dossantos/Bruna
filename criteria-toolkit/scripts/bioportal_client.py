#!/usr/bin/env python3
"""
bioportal_client.py

Use the BioPortal REST API (https://data.bioontology.org) to gloss clinical
terms in a policy. Unlike the UMLS client, BioPortal's Annotator AUTO-DETECTS
the clinical terms in free text, so you don't have to supply a term list.

Pipeline for glossing:
  1. Annotator  — find clinical concepts in the policy text (auto term extraction)
  2. Search     — fetch a plain-language definition for each (NCIT has the best text)

Auth (any of these; no ticket flow):
  header  Authorization: apikey token=<key>
  Key is read from, in order:
    1. --api-key
    2. env var BIOPORTAL_API_KEY
    3. ~/Claude/Projects/Credentials/BioPortal_API.txt

Commands:
  python3 bioportal_client.py recommend policy.md     # which ontologies fit the text
  python3 bioportal_client.py glossary  policy.md      # auto-detect terms -> glossary
  python3 bioportal_client.py annotate  policy.md      # auto-detect -> footnoted policy
  python3 bioportal_client.py define    "aneurysm"     # one term -> definition
"""

import os
import re
import sys
import html
import argparse
from pathlib import Path

import requests

BASE = "https://data.bioontology.org"
KEY_FILE = Path.home() / "Claude/Projects/Credentials/BioPortal_API.txt"

# Ontologies for definition text, best-first. NCIT carries clean plain-language
# definitions; SNOMEDCT/MSH are strong for detection but sparse on definition text.
DEFINITION_ONTOLOGIES = ["NCIT", "MSH", "MEDLINEPLUS", "OCHV"]

# Detection ontologies — broad clinical coverage.
DETECT_ONTOLOGIES = "SNOMEDCT,NCIT"

# UMLS semantic types that keep the Annotator to clinically-meaningful concepts
# (disease, sign/symptom, neoplasm, injury, congenital abnormality, dx procedure,
#  finding, pathologic function, body part). Cuts noise like "greater than".
CLINICAL_SEMANTIC_TYPES = "T047,T184,T191,T037,T019,T060,T033,T046,T023"


class BioPortalError(RuntimeError):
    pass


class BioPortalClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or self._resolve_key()
        if not self.api_key:
            raise BioPortalError(
                "No BioPortal API key found. Pass --api-key, set BIOPORTAL_API_KEY, "
                f"or write the key to {KEY_FILE}"
            )
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"apikey token={self.api_key}"
        self._def_cache: dict[str, dict | None] = {}

    @staticmethod
    def _resolve_key() -> str | None:
        env = os.environ.get("BIOPORTAL_API_KEY")
        if env:
            return env.strip()
        if KEY_FILE.exists():
            return KEY_FILE.read_text().strip()
        return None

    def _request(self, method: str, path: str, **kw):
        r = self.session.request(method, f"{BASE}{path}", timeout=60, **kw)
        if r.status_code == 401:
            raise BioPortalError("401 Unauthorized — the API key was rejected.")
        r.raise_for_status()
        return r.json()

    def recommend(self, text: str, top: int = 5):
        """Return the ontologies that best cover the text, best-first."""
        data = self._request("POST", "/recommender", data={"input": text, "input_type": 1})
        out = []
        for rec in data[:top]:
            out.append({
                "ontologies": [o["acronym"] for o in rec.get("ontologies", [])],
                "score": rec.get("evaluationScore"),
                "coverage": rec.get("coverageResult", {}).get("normalizedScore"),
            })
        return out

    def detect(self, text: str, semantic_types: str = CLINICAL_SEMANTIC_TYPES):
        """
        Auto-detect clinical concepts in free text. Returns one entry per distinct
        surface term (a word maps to several ontology classes; we keep the first,
        which avoids duplicate rows and wrong-sense collisions):
          {label, class_id, ontology, surfaces:[matched string], pos}
        """
        data = self._request("POST", "/annotator", data={
            "text": text,
            "ontologies": DETECT_ONTOLOGIES,
            "semantic_types": semantic_types,
            "longest_only": "true",
            "include": "prefLabel",
        })
        by_surface: dict[str, dict] = {}
        for a in data:
            cls = a["annotatedClass"]
            for m in a["annotations"]:
                surf = m["text"]
                key = surf.lower()
                pos = m.get("from", 1e9)
                # keep the earliest-position class for each surface term
                if key not in by_surface or pos < by_surface[key]["pos"]:
                    by_surface[key] = {
                        "label": cls.get("prefLabel") or surf,
                        "class_id": cls["@id"],
                        "ontology": cls["links"]["ontology"].split("/")[-1],
                        "surfaces": [surf],
                        "pos": pos,
                    }
        return sorted(by_surface.values(), key=lambda e: e["pos"])

    def define(self, term: str) -> dict:
        """Best plain-language definition for a term. Returns {term, label, source, definition}."""
        if term.lower() in self._def_cache:
            cached = self._def_cache[term.lower()]
            return cached if cached else {"term": term, "label": None, "source": None, "definition": None}
        for ont in DEFINITION_ONTOLOGIES:
            data = self._request("GET", "/search", params={
                "q": term, "ontologies": ont,
                "include": "prefLabel,definition",
                "require_definitions": "true", "pagesize": 1,
            })
            coll = data.get("collection", [])
            if coll and coll[0].get("definition"):
                res = {"term": term, "label": coll[0].get("prefLabel"),
                       "source": ont, "definition": _clean(coll[0]["definition"][0])}
                self._def_cache[term.lower()] = res
                return res
        self._def_cache[term.lower()] = None
        return {"term": term, "label": None, "source": None, "definition": None}

    def gloss(self, text: str):
        """Full pipeline: auto-detect terms, then attach a definition to each."""
        out = []
        for c in self.detect(text):
            d = self.define(c["label"])
            out.append({**c, "source": d["source"], "definition": d["definition"]})
        return out


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _read_text(path: str) -> str:
    return Path(path).read_text()


def cmd_recommend(client, args):
    for i, rec in enumerate(client.recommend(_read_text(args.file)), 1):
        onts = ",".join(rec["ontologies"])
        print(f"{i}. {onts:14} score={rec['score']:.3f}  coverage={rec['coverage']}")


def cmd_define(client, args):
    res = client.define(args.term)
    if res["definition"]:
        print(f"{res['term']} -> {res['label']}  [{res['source']}]")
        print(res["definition"])
    else:
        print(f"No definition found for: {args.term}")


def cmd_glossary(client, args):
    print("## Clinical terms glossary (auto-detected)\n")
    for c in client.gloss(_read_text(args.file)):
        surf = c["surfaces"][0]
        if c["definition"]:
            print(f"- **{surf}** ({c['label']}) — {c['definition']} "
                  f"_(BioPortal {c['ontology']}→{c['source']})_")
        else:
            print(f"- **{surf}** ({c['label']}) — _(detected in {c['ontology']}; "
                  f"no definition text — needs a manual gloss)_")


def cmd_annotate(client, args):
    text = _read_text(args.file)
    notes = []
    for i, c in enumerate(client.gloss(text), 1):
        gloss = c["definition"] or "(no definition text found)"
        placed = False
        for surf in c["surfaces"]:
            pat = re.compile(rf"\b({re.escape(surf)})\b", re.IGNORECASE)
            text, n = pat.subn(rf"\1[^{i}]", text, count=1)
            if n:
                placed = True
                break
        if placed:
            src = f" (BioPortal {c['ontology']}→{c['source']})" if c["definition"] else ""
            notes.append(f"[^{i}]: **{c['label']}** — {gloss}{src}")
    print(text)
    if notes:
        print("\n---\n")
        print("\n".join(notes))


def main(argv=None):
    p = argparse.ArgumentParser(description="BioPortal clinical-term glossing")
    p.add_argument("--api-key")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, helptext in [("recommend", "which ontologies fit a text"),
                           ("glossary", "auto-detect terms -> glossary"),
                           ("annotate", "auto-detect -> footnoted policy")]:
        s = sub.add_parser(name, help=helptext)
        s.add_argument("file")
    d = sub.add_parser("define", help="one term -> definition")
    d.add_argument("term")

    args = p.parse_args(argv)
    client = BioPortalClient(api_key=args.api_key)
    {"recommend": cmd_recommend, "glossary": cmd_glossary,
     "annotate": cmd_annotate, "define": cmd_define}[args.cmd](client, args)


if __name__ == "__main__":
    try:
        main()
    except BioPortalError as e:
        sys.exit(f"ERROR: {e}")
