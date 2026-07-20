#!/usr/bin/env python3
"""Feed a validated payer→project mapping back into the crosswalk (source of truth).

Reads an edited `Payer_Project_Mapping_<date>.csv` (or any CSV with the same key columns),
takes every row Bruna marked in the `validated` column, and appends/updates the matching entry
in `payer_project_crosswalk.csv`. Those entries then win automatically on the next reconcile run.

A row is applied when its `validated` cell is truthy (x / y / yes / true / 1). The project used is
whatever is in `resolved_project` — so Bruna can validate an auto-mapped row as-is, or correct the
project on a low/zero-confidence row first and then mark it validated. The UUID is taken from
`project_uuid` if present, else looked up by project name in insurance_projects.csv.

Backs up the crosswalk before writing. Idempotent: re-feeding the same file is a no-op.

Usage:
  python3 apply_feedback.py "<validated mapping>.csv" [--dry-run]
  python3 apply_feedback.py "<validated mapping>.csv" --crosswalk <path> --projects <path>
"""
import csv, os, sys, shutil, datetime, argparse

HOME=os.path.expanduser("~")
MASTER=f"{HOME}/Documents/Claude/Projects/Linear Master Data"
CROSSWALK=f"{MASTER}/payer_project_crosswalk.csv"
PROJECTS=f"{MASTER}/insurance_projects.csv"
XCOLS=["payer_family","insurance_payer","plan_category","linear_project","project_uuid","source","effective"]
TRUTHY={"x","y","yes","true","1","✓","validated"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("feedback"); ap.add_argument("--crosswalk",default=CROSSWALK)
    ap.add_argument("--projects",default=PROJECTS); ap.add_argument("--dry-run",action="store_true")
    a=ap.parse_args()
    stamp=datetime.date.today().isoformat(); month=stamp[:7]

    projects={r['Name'].strip():r['UUID'].strip() for r in csv.DictReader(open(a.projects))}

    xrows=[]; xindex={}
    if os.path.exists(a.crosswalk):
        for r in csv.DictReader(open(a.crosswalk)):
            xrows.append(r)
            xindex[(r['payer_family'].strip(),r['insurance_payer'].strip(),r['plan_category'].strip())]=r
    else:
        print(f"WARNING: crosswalk not found at {a.crosswalk} — creating a new one.")

    added=updated=skipped_unmarked=skipped_same=0; problems=[]
    for r in csv.DictReader(open(a.feedback)):
        if (r.get("validated") or "").strip().lower() not in TRUTHY:
            skipped_unmarked+=1; continue
        fam=(r.get("payer_family") or "").strip()
        pay=(r.get("insurance_payer") or "").strip()
        cat=(r.get("plan_category") or "").strip()
        proj=(r.get("resolved_project") or "").strip()
        uuid=(r.get("project_uuid") or "").strip() or projects.get(proj,"")
        if not proj:
            problems.append(f"  no project set for validated row: {fam} | {pay} | {cat}"); continue
        if not uuid:
            problems.append(f"  project '{proj}' not found in projects list: {fam} | {pay} | {cat}"); continue
        key=(fam,pay,cat)
        newrow={"payer_family":fam,"insurance_payer":pay,"plan_category":cat,
                "linear_project":proj,"project_uuid":uuid,
                "source":"Bruna-validated","effective":month}
        if key in xindex:
            ex=xindex[key]
            if ex.get("linear_project","").strip()==proj:
                skipped_same+=1; continue
            ex.update(newrow); updated+=1
        else:
            xrows.append(newrow); xindex[key]=newrow; added+=1

    print(f"validated rows applied: +{added} added, ~{updated} updated "
          f"(unchanged {skipped_same}, unmarked {skipped_unmarked})")
    if problems:
        print(f"{len(problems)} validated row(s) could NOT be applied (fix and re-feed):")
        for p in problems[:20]: print(p)

    if a.dry_run:
        print("\n--dry-run: crosswalk NOT modified."); return
    if added==0 and updated==0:
        print("\nnothing to write — crosswalk unchanged."); return

    if os.path.exists(a.crosswalk):
        bak=f"{a.crosswalk}.bak_{stamp}"; shutil.copy2(a.crosswalk,bak)
        print(f"\nbacked up crosswalk → {bak}")
    with open(a.crosswalk,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=XCOLS,extrasaction="ignore"); w.writeheader(); w.writerows(xrows)
    print(f"wrote {len(xrows)} crosswalk rows → {a.crosswalk}")
    print("These now win automatically on the next reconcile run.")

if __name__=="__main__":
    main()
