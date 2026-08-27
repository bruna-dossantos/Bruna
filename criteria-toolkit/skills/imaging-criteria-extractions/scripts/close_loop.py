#!/usr/bin/env python3
"""
close_loop.py  —  the find → fix → re-check controller

Runs the completeness loop as one command: apply the resolver's operational
definitions, then CHECK for (a) undefined decisive terms with no resolution and
(b) uncovered CLINICAL rules. If both are clean it's converged; otherwise it emits
a worklist of exactly what still needs authoring (the model/config-owner tops up
resolutions.json or re-authors the gap criteria, then re-runs). On convergence
(or with --render) it regenerates the full downstream so everything stays in sync.

Two modes:
  • default        — check-only. Emits a worklist and stops; a human/model authors
                     the fixes, then re-runs. Authoring stays in the loop by design.
  • --best-effort  — never dead-ends. Any term still undefined is AUTO-STUBBED with a
                     loud "PENDING — REQUIRED" flag (treated as NOT met), any residual
                     clinical gap is AUTO-ACCEPTED, and the full package is ALWAYS
                     rendered, plus a "NEEDS REVIEW" list of everything auto-handled.
                     The agent authors real fixes across re-runs to shrink that list;
                     this guarantees a finished, reviewable package every time.

Usage:
  close_loop.py criteria.json --inventory inv.json --resolutions res.json \
      --codes codes.csv --out-dir DIR [--pyv /path/to/venv/python] [--render] \
      [--best-effort]
"""

import re
import sys
import json
import copy
import argparse
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import resolve_ambiguous_terms as R      # noqa: E402
import coverage_check as CC              # noqa: E402

GAP = 0.4  # below this coverage = a gap


def crit_text(doc):
    out = []
    for g in (doc.get("groups") or [{"codes": doc.get("codes", [])}]):
        for c in g["codes"]:
            for ot in (c.get("order_types") or [{"criteria": c.get("criteria", [])}]):
                for cr in ot.get("criteria", []):
                    out.append(cr.get("title", "") + " " + cr.get("definition", ""))
    return " ".join(out)


def unresolved_terms(base, resolutions):
    # detect on the PRE-resolution criteria — the operational-definition prose the
    # resolver injects itself contains lexicon words ("stable", "focal"), which would
    # otherwise re-trigger as fresh "undefined" terms and prevent convergence.
    have = [r["term"].lower() for r in resolutions]
    def covered(term):
        t = term.lower()
        # resolved if exactly matched, or a phrase resolution subsumes it ("focal" ⊂ "focal problem")
        return any(t == h or t in h or h in t for h in have)
    return [t for t in R.detect(base, skip_resolved=True)
            if t["status"] != "policy_defined" and not covered(t["term"])]


def clinical_gaps(resolved, inventory):
    rules = [r for r in inventory["rules"] if r.get("relevance", "clinical") == "clinical"]
    rows = CC.check_inventory(crit_text(resolved), rules)
    return [r for r in rows if r["score"] < GAP]


def run(cmd, py):
    subprocess.run([py] + cmd, check=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Completeness loop controller")
    ap.add_argument("criteria_json")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--resolutions", required=True)
    ap.add_argument("--codes", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--accepted-gaps", help="JSON [{id,reason}] of residual gaps a reviewer "
                                            "has accepted (out-of-scope / matcher-miss)")
    ap.add_argument("--pyv", default=sys.executable, help="python with docx/reportlab/pdfplumber")
    ap.add_argument("--pdfs", nargs="*", default=[], help="source PDFs for traceability")
    ap.add_argument("--render", action="store_true", help="regenerate full downstream on convergence")
    ap.add_argument("--best-effort", action="store_true",
                    help="never dead-end: auto-stub still-undefined terms (loud PENDING flag) "
                         "and auto-accept residual gaps, then always render a complete package "
                         "+ a NEEDS-REVIEW list. The agent authors real fixes across re-runs to "
                         "shrink that list; this guarantees a finished package every time.")
    ap.add_argument("--max-passes", type=int, default=3)
    ap.add_argument("--organize", action="store_true",
                    help="after rendering, package the out-dir into a named run folder "
                         "(needs --theme and --payor)")
    ap.add_argument("--theme", help='product/service theme for the run folder, e.g. "MRI Head & Neck"')
    ap.add_argument("--payor", help='payor for the run folder, e.g. "Medicare"')
    ap.add_argument("--policy-id", help="policy id for the run folder (default: the LCD from the criteria)")
    args = ap.parse_args(argv)
    if args.organize and (not args.theme or not args.payor):
        ap.error("--organize needs --theme and --payor")

    base = json.loads(Path(args.criteria_json).read_text())
    inv = json.loads(Path(args.inventory).read_text())
    resolutions = json.loads(Path(args.resolutions).read_text())
    accepted = {}
    if args.accepted_gaps:
        accepted = {a["id"]: a.get("reason", "") for a in json.loads(Path(args.accepted_gaps).read_text())}
    out = Path(args.out_dir)
    lcd = base.get("policy", {}).get("lcd", "policy")

    passes, converged = [], False
    resolved = None
    for i in range(1, args.max_passes + 1):
        resolved = copy.deepcopy(base)
        R.apply(resolved, resolutions)
        unres = unresolved_terms(base, resolutions)   # detect on pre-resolution text
        gaps = clinical_gaps(resolved, inventory=inv)
        unaccepted = [g for g in gaps if g["id"] not in accepted]
        passes.append({"pass": i, "unresolved_terms": len(unres),
                       "clinical_gaps": len(gaps), "unaccepted": len(unaccepted)})
        print(f"pass {i}: {len(unres)} undefined terms w/o resolution, "
              f"{len(unaccepted)} unaccepted clinical gaps ({len(accepted)} accepted)",
              file=sys.stderr)
        if not unres and not unaccepted:
            converged = True
            break
        # pure code can't author real definitions/criteria — hand back a worklist and stop.
        break

    # BEST-EFFORT: never dead-end. Auto-stub still-undefined terms with a loud PENDING
    # flag, auto-accept residual gaps, re-apply, and finish. The agent authors real
    # fixes across re-runs; this guarantees a rendered package every time.
    auto_stubbed, auto_accepted = [], []
    if args.best_effort and not converged:
        unres = unresolved_terms(base, resolutions)
        gaps = clinical_gaps(resolved, inv)
        for t in unres:
            resolutions.append({
                "term": t["term"], "status": "resolved_by_interpretation",
                "operational_definition": {
                    "rule": ("⚠ AUTO-STUB — no operational definition authored yet; a reviewer "
                             "must define what counts as TRUE (time window + missing-data rule)"),
                    "missing_data_handling": "treat as NOT met until a reviewer defines it"},
                "provenance": {"decided_by": "auto-stub (best-effort)", "reviewer": "PENDING — REQUIRED"}})
            auto_stubbed.append(t["term"])
        for g in gaps:
            if g["id"] not in accepted:
                accepted[g["id"]] = "auto-accepted (best-effort) — PENDING review"
                auto_accepted.append(g["id"])
        resolved = copy.deepcopy(base)
        R.apply(resolved, resolutions)
        converged = True   # best-effort finish (residuals flagged for review, not dropped)

    # write the resolved criteria as canonical
    resolved_path = out / f"{lcd}_criteria.resolved.json"
    resolved_path.write_text(json.dumps(resolved, indent=2))

    # loop report + worklist
    conv_label = "YES" if converged else "NO — worklist below"
    if args.best_effort and (auto_stubbed or auto_accepted):
        conv_label = "YES (best-effort) — some items AUTO-HANDLED, review below"
    rep = [f"# Close-loop report — {lcd}", "",
           f"- Converged: **{conv_label}**",
           f"- Passes: {len(passes)}  |  " + "; ".join(
               f"pass {p['pass']}: {p['unresolved_terms']} undefined, {p['clinical_gaps']} gaps"
               for p in passes), ""]
    gaps = clinical_gaps(resolved, inv)
    unres = unresolved_terms(base, resolutions)
    unaccepted = [g for g in gaps if g["id"] not in accepted]
    if not converged:
        if unres:
            rep.append("## Undefined decisive terms — author an operational definition (add to resolutions.json)")
            for t in unres:
                rep.append(f"- **{t['term']}** in {t['criterion_title']}")
            rep.append("")
        if unaccepted:
            rep.append("## Clinical rules not covered — re-author a criterion, or accept (out-of-scope / matcher-miss)")
            for gp in unaccepted:
                rep.append(f"- **{gp['id']}** [{gp.get('type')}] {gp['sentence'][:110]}")
            rep.append("")
        rep.append("_Author the fixes / accept residuals, then re-run close_loop._")
    else:
        rep.append("No undefined terms and no unaccepted clinical gaps. Converged — safe to render.")
    if auto_stubbed or auto_accepted:
        rep.append("\n## ⚠ NEEDS REVIEW — auto-handled to finish the package (best-effort)")
        rep.append("_These were not confidently resolved. The package still rendered, but a "
                   "reviewer must confirm each. Author real fixes in resolutions.json / "
                   "accepted_gaps.json and re-run to clear them._")
        if auto_stubbed:
            rep.append("\n**Terms auto-stubbed (no operational definition yet — treated as NOT met):**")
            for term in auto_stubbed:
                rep.append(f"- {term}")
        if auto_accepted:
            rep.append("\n**Clinical gaps auto-accepted (no criterion authored yet):**")
            for gid in auto_accepted:
                rep.append(f"- {gid} — {next((g['sentence'][:110] for g in gaps if g['id']==gid), '')}")
    if accepted:
        rep.append("\n## Accepted residual gaps (reviewed, not fixed)")
        for gid, reason in accepted.items():
            rep.append(f"- **{gid}** — {reason}")
    (out / f"{lcd}_close_loop_report.md").write_text("\n".join(rep))
    print(f"wrote {resolved_path.name} and {lcd}_close_loop_report.md", file=sys.stderr)

    if args.render or (args.best_effort and converged):
        cj = str(resolved_path)
        print("regenerating full downstream from the resolved criteria…", file=sys.stderr)
        run([str(HERE / "render_criteria_docx.py"), cj, "--out", str(out / f"{lcd}_criteria_by_code.docx")], args.pyv)
        run([str(HERE / "render_criteria_pdf.py"), cj, "--out", str(out / f"{lcd}_criteria_by_code.pdf")], args.pyv)
        subprocess.run([sys.executable, str(HERE / "render_criteria_doc.py"), cj],
                       check=True, stdout=open(out / f"{lcd}_criteria_by_code.md", "w"))
        run([str(HERE / "build_extraction_fields.py"), cj, "--out", str(out / f"{lcd}_extraction_fields.csv")], sys.executable)
        # ontology-grounding review/accept surface: bucket every recall concept by how much
        # human review it needs (must_author / ungrounded / fuzzy_icd / grounded_ok).
        run([str(HERE / "build_extraction_review.py"), str(out / f"{lcd}_extraction_fields.csv"),
             "--out-md", str(out / f"{lcd}_extraction_review.md"),
             "--out-csv", str(out / f"{lcd}_extraction_review.csv")], sys.executable)
        run([str(HERE / "render_extractions_doc.py"), str(out / f"{lcd}_extraction_fields.csv"),
             "--out-md", str(out / f"{lcd}_extraction_fields_by_code.md"),
             "--out-docx", str(out / f"{lcd}_extraction_fields_by_code.docx")], args.pyv)
        run([str(HERE / "build_traceability.py"), args.inventory, cj, "--out", str(out / f"{lcd}_traceability.json")], sys.executable)
        if args.pdfs:
            # locate rules in the source PDFs FIRST — both HTML renderers require
            # {lcd}_rule_locations.json, and nothing else generates it. Needs pdfplumber (pyv).
            run([str(HERE / "locate_rules_in_pdf.py"), args.inventory,
                 "--pdf"] + args.pdfs + ["--out", str(out / f"{lcd}_rule_locations.json")], args.pyv)
            run([str(HERE / "render_traceability_html.py"), str(out / f"{lcd}_traceability.json"),
                 "--locations", str(out / f"{lcd}_rule_locations.json"), "--pdf"] + args.pdfs
                + ["--title", lcd, "--out", str(out / f"{lcd}_traceability.html")], sys.executable)
            run([str(HERE / "render_criteria_explorer.py"), cj,
                 "--traceability", str(out / f"{lcd}_traceability.json"),
                 "--locations", str(out / f"{lcd}_rule_locations.json"), "--pdf"] + args.pdfs
                + ["--title", lcd, "--out", str(out / f"{lcd}_criteria_explorer.html")], sys.executable)
        run([str(HERE / "build_machine_copy.py"), cj, "--codes", args.codes, "--out-dir", str(out)], sys.executable)
        print("downstream regenerated.", file=sys.stderr)

    if args.organize:
        import organize_run as ORG
        run_dir = ORG.organize(str(out), args.theme, args.payor,
                               args.policy_id or lcd, in_place=False)
        print(f"packaged run into {run_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
