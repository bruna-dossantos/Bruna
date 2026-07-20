#!/usr/bin/env python3
"""Reconcile a Service-Line Order-Type export against Linear criteria tickets. READ-ONLY.

Resolution order per row:
  1. Crosswalk override (Bruna's source of truth)  -> payer_project_crosswalk.csv
  2. Family + category (+ state)                    -> resolver.resolve_family
  3. Order-name mining                              -> resolver.resolve_ordername
  4. LOB-guarded name normalizer (exact / unique)   -> vs projects list
Then classifies each (code|drug x project) vs the tickets export:
  DONE / FLIP / CONFLICT / NEW-TIX / UNIT-GAP, and lists unresolved rows for review.

Usage: python3 reconcile.py "<order type export>.csv"
"""
import csv, re, sys, os, datetime
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolver as R

HOME=os.path.expanduser("~")
MASTER=f"{HOME}/Documents/Claude/Projects/Linear Master Data"
OUT=f"{HOME}/Documents/Claude/Projects/Criteria Updates"
WORKDIR=f"{OUT}/.recon_work"          # payer source lists + payer-linear-mapper output live here
CROSSWALK=f"{MASTER}/payer_project_crosswalk.csv"
PROJECTS=f"{MASTER}/insurance_projects.csv"
TICKETS=f"{MASTER}/insurance_initiative_issues_latest.csv"
DONE_STATES={"Done","AutoGen: Done"}
FLIPPABLE={"Not Started","In Progress","In Review","Reviewed - Needs Revision","Policy Research"}

def norm(s): return re.sub(r'[^a-z0-9]+','',(s or '').lower())
def pnorm(s):
    s=(s or '').lower(); s=re.sub(r'\b(of|the|inc|llc|company|health\s?plan)\b','',s)
    s=s.replace("blue cross blue shield","bcbs"); return re.sub(r'[^a-z0-9]+','',s)
def slug(n): return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',(n or '').lower())).strip('-')
def clean_code(c):
    m=re.match(r'\s*([A-Z]\d{3,4}[A-Z]?|\d{4,5}[A-Z]?)',(c or '').strip())
    return m.group(1) if m else (c or '').strip()

def prep(src):
    """Emit per-service-line distinct-payer source lists for the payer-linear-mapper skill."""
    from collections import Counter as C, defaultdict as dd
    os.makedirs(WORKDIR, exist_ok=True)
    rows=list(csv.DictReader(open(src)))
    made=[]
    for cat,fname in [("DME","dme_payers_source.csv"),("Infusion","inf_payers_source.csv")]:
        vol=C(); domc=dd(C)
        for r in rows:
            if r['service_line_category']!=cat: continue
            p=r['insurance_payer'].strip()
            if not p: continue
            vol[p]+=1; domc[p][r['plan_category']]+=1
        with open(f"{WORKDIR}/{fname}","w",newline="") as f:
            w=csv.writer(f); w.writerow(["payer_name","volume","dominant_plan_category"])
            for p,v in vol.most_common(): w.writerow([p,v,domc[p].most_common(1)[0][0]])
        made.append((fname,len(vol)))
    print("Wrote payer source lists to", WORKDIR)
    for fn,n in made: print(f"  {fn}: {n} distinct payers")
    print("\nNEXT: run the payer-linear-mapper skill on each, writing outputs back to this dir:")
    print(f'  map_payers.py --source "{WORKDIR}/dme_payers_source.csv" --out "{WORKDIR}/dme_mapping.csv" --service-line dme')
    print(f'  map_payers.py --source "{WORKDIR}/inf_payers_source.csv" --out "{WORKDIR}/inf_mapping.csv" --service-line other')
    print("Then re-run:  python3 reconcile.py \"<export>\"")

def load_mapper(projset):
    """Load payer-linear-mapper output (if present) as a name->project layer. conf>=2, LOB check at use."""
    m={}
    for fn in ["dme_mapping.csv","inf_mapping.csv"]:
        p=f"{WORKDIR}/{fn}"
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p)):
            src=r.get('source','').strip(); proj=r.get('project','').strip()
            try: conf=int(r.get('confidence',0))
            except: conf=0
            # defensive: guard against the known Arkansas->Kansas mapper bug
            if src=="Blue Cross Blue Shield of Arkansas" and "Blue Cross Blue Shield (Arkansas)" in projset:
                proj="Blue Cross Blue Shield (Arkansas)"; conf=3
            if proj and conf>=2 and proj in projset: m.setdefault(src,proj)
    return m

def main(src):
    stamp=datetime.date.today().isoformat()
    # ---- reference data ----
    projects={r['Name']:r['UUID'] for r in csv.DictReader(open(PROJECTS))}
    projset=set(projects); slug2name={slug(n):n for n in projects}
    nproj=defaultdict(list)
    for n in projset: nproj[pnorm(n)].append(n)
    # crosswalk (source of truth)
    xwalk={}
    if os.path.exists(CROSSWALK):
        for r in csv.DictReader(open(CROSSWALK)):
            key=(r['payer_family'].strip(), r['insurance_payer'].strip(), r['plan_category'].strip())
            xwalk[key]=(r['linear_project'].strip(), r['project_uuid'].strip())
    else:
        print(f"WARNING: crosswalk not found at {CROSSWALK}")

    # ---- freshness gate ----
    if os.path.exists(TICKETS):
        age=(datetime.datetime.now()-datetime.datetime.fromtimestamp(os.path.getmtime(TICKETS))).days
        print(f"tickets export age: {age} day(s) ({TICKETS})")
        if age>7:
            print("  ** STALE (>7d): run linear-ops:linear-master-data (chains refresh-insurance-issues) before trusting verdicts. **")
    else:
        print(f"ERROR: tickets export missing at {TICKETS} — run linear-ops:linear-master-data first."); return

    # ---- Linear ticket index ----
    dme_idx=defaultdict(list); drug_idx=defaultdict(list)
    for r in csv.DictReader(open(TICKETS)):
        proj=r['Project'].strip()
        url=r.get('URL') or f"https://linear.app/tennr-product/issue/{r['Identifier']}"
        ref={"id":r['Identifier'],"state":r['State'].strip(),"url":url}
        if r['Team']=='DME Criteria':
            c=clean_code(r['Title'])
            if c: dme_idx[(c,proj)].append(ref)
        elif r['Team']=='Drugs Criteria':
            drug_idx[(norm(r['Title']),proj)].append(ref)
    lin_codes={c for c,_ in dme_idx}; lin_drugs={d for d,_ in drug_idx}

    mapper=load_mapper(projset)   # payer-linear-mapper output layer (name -> project)
    print(f"payer-linear-mapper entries loaded: {len(mapper)}" + ("" if mapper else "  (none — run the mapper step for higher coverage)"))

    def name_resolve(payer,cat):
        payer=(payer or '').strip()
        if not payer: return (None,None)
        if payer in mapper and R.lob_ok(cat,mapper[payer]): return (mapper[payer],"name:mapper")
        cands=([payer] if payer in projset else [])+(nproj[pnorm(payer)] if len(nproj.get(pnorm(payer),[]))==1 else [])
        for c in cands:
            return (c,"name:norm") if R.lob_ok(cat,c) else (None,None)
        return (None,None)

    # ---- resolve every row ----
    rows=list(csv.DictReader(open(src)))
    res=[]; basis_ct=Counter()
    for r in rows:
        fam=r['payer_family'].strip(); pay=r['insurance_payer'].strip(); cat=r['plan_category'].strip()
        orn=r['order_rule_name']; proj=None; basis=None
        if (fam,pay,cat) in xwalk and xwalk[(fam,pay,cat)][0]:
            proj,basis=xwalk[(fam,pay,cat)][0],"crosswalk"
        if not proj:
            p,m=R.resolve_family(fam,cat,pay,orn,projset)
            if p: proj,basis=p,m
            else:
                p2,m2=R.resolve_ordername(orn,projset,slug2name,slug)
                if p2 and R.lob_ok(cat,p2): proj,basis=p2,m2
                else:
                    nm,nb=name_resolve(pay,cat)
                    if nm: proj,basis=nm,nb
                    else: basis="unresolved:"+(m2 if m2.startswith("ordername") and m!="need-specific-payer" else m)
        basis_ct[basis]+=1
        res.append({**r,"resolved_project":proj or "","project_uuid":projects.get(proj,"") if proj else "","basis":basis})

    resolved=sum(1 for x in res if x["resolved_project"])
    print(f"\nresolved {resolved:,}/{len(rows):,} ({100*resolved/len(rows):.1f}%)")

    # ---- reconcile (DME->DME Criteria, Infusion->Drugs Criteria) ----
    buckets=Counter(); vol=Counter(); detail=[]
    for cat,is_dme,idx,univ in [("DME",True,dme_idx,lin_codes),("Infusion",False,drug_idx,lin_drugs)]:
        units=defaultdict(lambda:{"vol":0})
        for x in res:
            if x['service_line_category']!=cat or not x["resolved_project"]: continue
            k=clean_code(x['code']) if is_dme else x['service_line'].strip()
            units[(k,x["resolved_project"],x["basis"])]["vol"]+=1
        for (k,proj,basis),info in units.items():
            uk=k if is_dme else norm(k)
            refs=idx.get((uk,proj),[]); states=[a["state"] for a in refs]
            if (uk not in univ): verdict="UNIT-GAP"
            elif not states: verdict="NEW-TIX"
            elif any(s in DONE_STATES for s in states): verdict="DONE"
            elif any(s in FLIPPABLE for s in states): verdict="FLIP"
            else: verdict="CONFLICT"
            buckets[(cat,verdict)]+=1; vol[(cat,verdict)]+=info["vol"]
            detail.append({"service_line":cat,"unit":k,"project":proj,"basis":basis,"rows_built":info["vol"],
                "linear_states":";".join(sorted(set(states))),
                "ticket_ids":";".join(sorted({a["id"] for a in refs})),
                "ticket_urls":" ".join(sorted({a["url"] for a in refs})),"verdict":verdict})

    for c in ["DME","Infusion"]:
        print(f"\n{c}: "+" ".join(f"{v}={buckets[(c,v)]}" for v in ["DONE","FLIP","CONFLICT","NEW-TIX","UNIT-GAP"]))

    # ---- write outputs ----
    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/row_resolution_{stamp}.csv","w",newline="") as f:
        cols=["service_line_category","code","service_line","payer_family","insurance_payer","plan_category","resolved_project","project_uuid","basis"]
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(res)
    from build_workbook import build
    build(detail, res, buckets, vol, f"{OUT}/Order_Rule_Linear_Reconciliation_{stamp}.xlsx", stamp)
    # unique payer -> project mapping with confidence (standard output)
    from build_payer_mapping import build as build_mapping
    map_out, map_dist = build_mapping(res, WORKDIR,
        f"{OUT}/Payer_Project_Mapping_{stamp}.csv", f"{OUT}/Payer_Project_Mapping_{stamp}.xlsx")
    resolved_map=sum(1 for r in map_out if r["confidence"]>0)
    print(f"\npayer→project mapping: {len(map_out):,} unique combos "
          f"({resolved_map:,} resolved, {len(map_out)-resolved_map:,} unresolved) · "
          + " ".join(f"conf{k}={map_dist.get(k,0)}" for k in [5,4,3,2,0]))
    print(f"\nwrote:\n  {OUT}/Order_Rule_Linear_Reconciliation_{stamp}.xlsx\n  {OUT}/row_resolution_{stamp}.csv"
          f"\n  {OUT}/Payer_Project_Mapping_{stamp}.xlsx\n  {OUT}/Payer_Project_Mapping_{stamp}.csv")

if __name__=="__main__":
    args=sys.argv[1:]
    if not args:
        print("usage: python3 reconcile.py [--prep] \"<order type export>.csv\""); sys.exit(1)
    if args[0]=="--prep":
        prep(args[1])
    else:
        main(args[0])
