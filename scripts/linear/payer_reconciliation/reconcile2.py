#!/usr/bin/env python3
"""Reconciliation v2 on family-anchored resolution (row_resolution.csv). READ-ONLY."""
import csv, re, json
from collections import Counter, defaultdict

MD="/Users/brunadossantos/Claude/Projects/Linear Master Data"
LIN=f"{MD}/insurance_initiative_issues_latest.csv"
WORK="/private/tmp/claude-501/-Users-brunadossantos-Projects-Bruna--claude-worktrees-inspiring-cannon-a54635/b4e7b3c8-2754-46fa-a3ad-6e0e1f6f10f1/scratchpad/recon"

DONE_STATES={"Done","AutoGen: Done"}
FLIPPABLE={"Not Started","In Progress","In Review","Reviewed - Needs Revision","Policy Research"}
def norm(s): return re.sub(r'[^a-z0-9]+','',(s or '').lower())
def clean_code(c):
    m=re.match(r'\s*([A-Z]\d{3,4}[A-Z]?|\d{4,5}[A-Z]?)',(c or '').strip())
    return m.group(1) if m else (c or '').strip()

# ---- Linear cache ----
dme_idx=defaultdict(list); drug_idx=defaultdict(list)
for r in csv.DictReader(open(LIN)):
    proj=r['Project'].strip(); ref={"id":r['Identifier'],"state":r['State'].strip(),"url":r['URL']}
    if r['Team']=='DME Criteria':
        c=clean_code(r['Title'])
        if c: dme_idx[(c,proj)].append(ref)
    elif r['Team']=='Drugs Criteria':
        drug_idx[(norm(r['Title']),proj)].append(ref)
lin_codes={c for (c,p) in dme_idx}; lin_drugnorms={d for (d,p) in drug_idx}
def classify(states):
    if not states: return "NEW-TIX"
    if any(s in DONE_STATES for s in states): return "DONE"
    if any(s in FLIPPABLE for s in states): return "FLIP"
    return "CONFLICT"

# ---- units from resolution ----
rr=list(csv.DictReader(open(f"{WORK}/row_resolution.csv")))
buckets=Counter(); vol_buckets=Counter(); report=[]; unresolved=Counter(); unres_rows=Counter()

for cat,is_dme,idx in [("DME",True,dme_idx),("Infusion",False,drug_idx)]:
    units=defaultdict(lambda:{"vol":0})
    for r in rr:
        if r['service_line_category']!=cat: continue
        if not r['resolved_project']:
            unresolved[cat]+=1; unres_rows[(cat,r['basis'].replace('unresolved:',''))]+=1; continue
        k = clean_code(r['code']) if is_dme else r['service_line'].strip()
        units[(k,r['resolved_project'],r['basis'])]["vol"]+=1
    for (k,proj,basis),info in units.items():
        uk = k if is_dme else norm(k)
        in_univ = (uk in lin_codes) if is_dme else (uk in lin_drugnorms)
        refs=idx.get((uk,proj),[]); states=[x["state"] for x in refs]
        verdict = "UNIT-GAP" if not in_univ else classify(states)
        buckets[(cat,verdict)]+=1; vol_buckets[(cat,verdict)]+=info["vol"]
        report.append({"service_line":cat,"unit":k,"project":proj,"basis":basis,
            "rows_built":info["vol"],"linear_states":";".join(sorted(set(states))),
            "ticket_ids":";".join(sorted({x["id"] for x in refs})),
            "ticket_urls":" ".join(sorted({x["url"] for x in refs})),"verdict":verdict})

with open(f"{WORK}/reconciliation2_detail.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["service_line","unit","project","basis","rows_built","linear_states","ticket_ids","ticket_urls","verdict"])
    w.writeheader()
    for row in sorted(report,key=lambda x:(x['service_line'],x['verdict'],-x['rows_built'])): w.writerow(row)

for cat in ["DME","Infusion"]:
    print(f"\n===== {cat} =====")
    for v in ["DONE","FLIP","CONFLICT","NEW-TIX","UNIT-GAP"]:
        print(f"  {v:10} units={buckets[(cat,v)]:5}  built_rows={vol_buckets[(cat,v)]:6,}")
    print(f"  {'unresolved':10} rows={unresolved[cat]:,} (no project mapping)")
    for (c,reason),v in sorted(unres_rows.items(),key=lambda x:-x[1]):
        if c==cat: print(f"       {v:6,}  {reason}")

json.dump({"buckets":{f"{c}|{v}":buckets[(c,v)] for c,v in buckets},
           "vol_buckets":{f"{c}|{v}":vol_buckets[(c,v)] for c,v in vol_buckets},
           "unresolved":{c:unresolved[c] for c in unresolved}},
          open(f"{WORK}/summary2.json","w"),indent=2)
print("\nwrote reconciliation2_detail.csv + summary2.json")
