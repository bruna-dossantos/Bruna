#!/usr/bin/env python3
"""
locate_rules_in_pdf.py  —  anchor each rule to sharp per-line boxes in a source PDF

For click-through highlighting. For every rule, find which source PDF/page it came
from and TIGHT highlight rectangles that follow the matched phrase across lines
(not one loose union box). Method:
  1. pick the page with the most of the rule's content words (which PDF + page);
  2. align the rule's content-word sequence to that page's words in reading order
     (ordered subsequence with small gaps) to find the actual matched words;
  3. group matched words by line → one rectangle per line (sharp highlight).
Falls back to a term-union box if the phrase can't be aligned.

Requires pdfplumber (isolated venv if system Python is externally managed).

Usage:
  locate_rules_in_pdf.py rule_inventory.json --pdf a.pdf b.pdf --out rule_locations.json
"""

import re
import sys
import json
import argparse
from pathlib import Path

import pdfplumber

STOP = set("""the a an and or of to in for with without on at by is are was were be been being that
this these those which who whom whose when where while as such than then thus into onto from patient
patients used use using not no any all some other its it their his her when may can will shall should
would could per one two document documented record records medical given""".split())


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def content_seq(text):
    out = []
    for w in re.findall(r"\w+", text or ""):
        n = norm(w)
        if len(n) >= 4 and n not in STOP:
            out.append(n)
    return out[:40]


def index_pdf(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            words = []
            for w in pg.extract_words(use_text_flow=True):
                nw = norm(w["text"])
                if nw:
                    words.append((nw, float(w["x0"]), float(w["top"]),
                                  float(w["x1"]), float(w["bottom"])))
            pages.append({"words": words, "w": float(pg.width), "h": float(pg.height)})
    return pages


def align_rects(seq, words, max_skip=4):
    """Align content-word seq to page words (ordered, small gaps). Return matched
    word boxes, or None."""
    if not seq:
        return None
    wnorm = [w[0] for w in words]
    seqset = set(seq)
    best = None
    starts = [i for i, wn in enumerate(wnorm) if wn == seq[0]]
    for s in starts:
        matched = [s]
        j, k, skip = s, 1, 0
        while k < len(seq) and j < len(words) - 1:
            nxt = wnorm[j + 1]
            if nxt == seq[k]:
                j += 1; matched.append(j); k += 1; skip = 0
            else:
                j += 1
                skip += 1 if nxt in seqset or True else 0
                if skip > max_skip:
                    break
        score = len(matched)
        span = matched[-1] - matched[0] + 1
        cand = (score, -span, matched)
        if best is None or cand[:2] > best[:2]:
            best = cand
    if not best or best[0] < max(2, len(seq) // 4):
        return None
    return [words[i] for i in best[2]]


def line_rects(matched):
    """Group matched words into per-line rectangles."""
    lines = {}
    for _, x0, top, x1, bottom in matched:
        key = round(top / 3)  # cluster by ~3pt bands = same visual line
        b = lines.setdefault(key, [x0, top, x1, bottom])
        b[0] = min(b[0], x0); b[1] = min(b[1], top); b[2] = max(b[2], x1); b[3] = max(b[3], bottom)
    rects = [[round(v, 1) for v in r] for r in lines.values()]
    rects.sort(key=lambda r: (r[1], r[0]))
    return rects


def locate(rule, pdf_index):
    terms = {norm(t) for t in (rule.get("key_terms") or []) if norm(t)}
    seq = content_seq(rule.get("text", ""))
    if not terms and not seq:
        return None
    # 1) pick pdf+page by term hit count
    best_page = None
    for pdf_name, pages in pdf_index.items():
        for pi, page in enumerate(pages):
            page_terms = {w[0] for w in page["words"]}
            hits = len(terms & page_terms) if terms else 0
            if best_page is None or hits > best_page[0]:
                best_page = (hits, pdf_name, pi, page)
    if not best_page or best_page[0] == 0:
        return None
    _, pdf_name, pi, page = best_page
    # 2) sharp phrase alignment on that page → per-line rects
    matched = align_rects(seq, page["words"])
    if matched:
        rects = line_rects(matched)
    else:
        # fallback: capped term-union box
        mw = [w for w in page["words"] if w[0] in terms]
        if not mw:
            return None
        tops = sorted(w[2] for w in mw)
        x0 = min(w[1] for w in mw); x1 = max(w[3] for w in mw)
        bottom = max(w[4] for w in mw if w[2] <= tops[0] + 120)
        rects = [[round(x0, 1), round(tops[0], 1), round(x1, 1), round(bottom, 1)]]
    conf = round(len(terms & {w[0] for w in page["words"]}) / len(terms), 2) if terms else 0.5
    return {"source_pdf": pdf_name, "page": pi + 1, "rects": rects,
            "bbox": [min(r[0] for r in rects), min(r[1] for r in rects),
                     max(r[2] for r in rects), max(r[3] for r in rects)],
            "page_w": round(page["w"], 1), "page_h": round(page["h"], 1),
            "confidence": conf, "sharp": bool(matched)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Anchor rules to sharp PDF rects")
    ap.add_argument("rule_inventory")
    ap.add_argument("--pdf", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    inv = json.loads(Path(args.rule_inventory).read_text())
    pdf_index = {Path(p).name: index_pdf(p) for p in args.pdf}
    locs, found, sharp = {}, 0, 0
    for r in inv["rules"]:
        loc = locate(r, pdf_index)
        if loc:
            locs[r["id"]] = loc; found += 1; sharp += 1 if loc["sharp"] else 0
    Path(args.out).write_text(json.dumps(locs, indent=2))
    print(f"located {found}/{len(inv['rules'])} rules ({sharp} sharp phrase-matched, "
          f"{found-sharp} fell back to term box); wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
