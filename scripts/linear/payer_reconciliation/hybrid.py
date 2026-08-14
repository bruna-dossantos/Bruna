#!/usr/bin/env python3
"""Hybrid resolver: family+category first, then name-based fallback (BCBS state-brands, catch-alls)."""
import csv, re
from collections import Counter, defaultdict
import family_lib as F

DL="/Users/brunadossantos/Downloads/Service Line Order Type Codes Jul 15 2026.csv"
PROJ="/Users/brunadossantos/Documents/Claude/Projects/Linear Master Data/insurance_projects.csv"
WORK="/private/tmp/claude-501/-Users-brunadossantos-Projects-Bruna--claude-worktrees-inspiring-cannon-a54635/b4e7b3c8-2754-46fa-a3ad-6e0e1f6f10f1/scratchpad/recon"
projset=F.projset
projects={r['Name']:r['UUID'] for r in csv.DictReader(open(PROJ))}

def pnorm(s):
    s=(s or '').lower()
    s=re.sub(r'\b(of|the|inc|llc|company|health\s?plan)\b','',s)
    s=s.replace("blue cross blue shield","bcbs")
    return re.sub(r'[^a-z0-9]+','',s)
nproj=defaultdict(list)
for name in projset: nproj[pnorm(name)].append(name)

# name-based mapper outputs (c2/c3) + Arkansas fix
resolver={}
for fn in ["dme_mapping.csv","inf_mapping.csv"]:
    for r in csv.DictReader(open(f"{WORK}/{fn}")):
        src=r['source'].strip(); proj=r['project'].strip()
        try: conf=int(r['confidence'])
        except: conf=0
        if src=="Blue Cross Blue Shield of Arkansas": proj="Blue Cross Blue Shield (Arkansas)"; conf=3
        if src=="Blue Cross Blue Shield of Michigan/ Medicare": proj=""; conf=1
        if proj and conf>=2 and proj in projset: resolver.setdefault(src,(proj,"name:mapper"))

def lob_ok(cat, proj):
    """Reject a name-based match that contradicts the row's line of business."""
    if not proj: return True
    pl=proj.lower()
    is_mcaid="medicaid" in pl or "mco" in pl
    is_ma=("medicare advantage" in pl) or (re.search(r'\bma\b',pl) is not None)
    is_mcare=("medicare" in pl) and not is_ma
    if cat=="COMMERCIAL" and (is_mcaid or is_ma or is_mcare): return False
    if cat=="MEDICAID" and not is_mcaid: return False
    if cat=="MEDICARE_ADVANTAGE" and not is_ma: return False
    if cat=="MEDICARE" and not (is_mcare or is_ma): return False
    return True

def name_resolve(payer, cat):
    payer=(payer or '').strip()
    if not payer: return (None,"none")
    for cand,tag in ([ (resolver[payer][0],resolver[payer][1]) ] if payer in resolver else []) \
                    + ([(payer,"name:exact")] if payer in projset else []) \
                    + ([(nproj[pnorm(payer)][0],"name:norm")] if len(nproj.get(pnorm(payer),[]))==1 else []):
        if lob_ok(cat,cand): return (cand,tag)
        return (None,f"needs-{cat.lower()}-project")   # name match exists but wrong LOB
    return (None,"name:unmapped")

rows=list(csv.DictReader(open(DL)))
basis=Counter(); resolved_rows=0
detail=[]
for r in rows:
    fam=r['payer_family']; cat=r['plan_category']; payer=r['insurance_payer']; orn=r['order_rule_name']
    proj,m=F.resolve(fam,cat,payer,orn)
    if proj:
        b=m
    else:
        proj,b=name_resolve(payer,cat)
        if not proj:
            # last resort: family+cat national even if state parse failed handled already; leave unresolved
            b="unresolved:"+m
    if proj: resolved_rows+=1
    basis[b]+=1
    detail.append((r,proj,b))

n=len(rows)
print(f"total rows {n:,}")
print(f"RESOLVED {resolved_rows:,} ({100*resolved_rows/n:.1f}%)   unresolved {n-resolved_rows:,} ({100*(n-resolved_rows)/n:.1f}%)")
print("\n=== resolution basis ===")
for b,v in basis.most_common():
    tag="  " if not b.startswith("unresolved") else "✗ "
    print(f"  {tag}{v:6,}  {b}")

# save row-level resolution for downstream reconcile
with open(f"{WORK}/row_resolution.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["service_line_category","code","service_line","payer_family","insurance_payer","plan_category","resolved_project","project_uuid","basis"])
    for r,proj,b in detail:
        w.writerow([r['service_line_category'],r['code'],r['service_line'],r['payer_family'],
                    r['insurance_payer'],r['plan_category'],proj or "",projects.get(proj,"") if proj else "",b])
print("\nwrote row_resolution.csv")
