#!/usr/bin/env python3
"""Family-anchored resolver: (payer_family, plan_category, [state]) -> Linear project."""
import csv, re
from collections import Counter, defaultdict

DL="/Users/brunadossantos/Downloads/Service Line Order Type Codes Jul 15 2026.csv"
PROJ="/Users/brunadossantos/Claude/Projects/Linear Master Data/insurance_projects.csv"
projset={r['Name'] for r in csv.DictReader(open(PROJ))}

STATES=['alabama','alaska','arizona','arkansas','california','colorado','connecticut','delaware',
 'florida','georgia','hawaii','idaho','illinois','indiana','iowa','kansas','kentucky','louisiana',
 'maine','maryland','massachusetts','michigan','minnesota','mississippi','missouri','montana',
 'nebraska','nevada','new hampshire','new jersey','new mexico','new york','north carolina',
 'north dakota','ohio','oklahoma','oregon','pennsylvania','rhode island','south carolina',
 'south dakota','tennessee','texas','utah','vermont','virginia','washington','west virginia',
 'wisconsin','wyoming','district of columbia']
ABBR={'oh':'ohio','tx':'texas','ca':'california','fl':'florida','ny':'new york','nj':'new jersey',
 'pa':'pennsylvania','il':'illinois','mi':'michigan','wa':'washington','az':'arizona','tn':'tennessee',
 'ak':'alaska','md':'maryland','nc':'north carolina','sc':'south carolina','ma':'massachusetts',
 'ok':'oklahoma','wv':'west virginia','nd':'north dakota','sd':'south dakota','wi':'wisconsin',
 'mo':'missouri','ne':'nebraska','ut':'utah','ga':'georgia','va':'virginia','id':'idaho',
 'ky':'kentucky','la':'louisiana','co':'colorado','ct':'connecticut','ri':'rhode island','hi':'hawaii',
 'ar':'arkansas','ia':'iowa','ks':'kansas','mt':'montana','nv':'nevada','nm':'new mexico','or':'oregon',
 'de':'delaware','me':'maine','nh':'new hampshire','vt':'vermont','mn':'minnesota','ms':'mississippi','in':'indiana'}
def parse_state(*texts):
    for t in texts:
        tl=(t or '').lower()
        for s in STATES:
            if re.search(r'\b'+re.escape(s)+r'\b',tl): return s
        for ab,full in ABBR.items():
            if re.search(r'\b'+ab+r'\b',tl): return full
    return None
def title(s): return " ".join(w.capitalize() for w in s.split())

# family + category -> single national project
NAT={
 'Aetna':{'COMMERCIAL':'Aetna','MEDICARE_ADVANTAGE':'Aetna Medicare Advantage'},
 'Cigna':{'COMMERCIAL':'Cigna'},
 'Humana':{'COMMERCIAL':'Humana','MEDICARE_ADVANTAGE':'Humana Medicare Advantage'},
 'United HealthCare (UHC)':{'COMMERCIAL':'United Healthcare Commercial','MEDICARE_ADVANTAGE':'United Healthcare Medicare Advantage'},
 'Molina Healthcare':{'COMMERCIAL':'Molina Healthcare','MEDICARE_ADVANTAGE':'Molina Medicare Advantage'},
 'Oscar Health':{'COMMERCIAL':'Oscar'},
 'Kaiser Permanente':{'COMMERCIAL':'KAISER PERMANENTE'},
}
def resolve(fam, cat, payer, orn):
    fam=(fam or '').strip(); cat=(cat or '').strip()
    # 1. Medicare FFS -> single project (family-agnostic)
    if cat=='MEDICARE':
        return ('Medicare','family+cat')
    # 2. national families by family+category
    if fam in NAT and cat in NAT[fam]:
        p=NAT[fam][cat]
        return (p,'family+cat') if p in projset else (None,'target-missing:'+p)
    # 3. BCBS -> per state
    if fam=='Blue Cross Blue Shield':
        st=parse_state(payer,orn)
        if not st:
            # orphan BCBS: no payer, no state anywhere -> default to Anthem BCBS (commercial only)
            if not (payer or '').strip():
                if cat=='COMMERCIAL' and 'Anthem Blue Cross Blue Shield' in projset:
                    return ('Anthem Blue Cross Blue Shield','family:bcbs-blank->anthem')
                return (None,'bcbs-blank-noncommercial-review')
            return (None,'bcbs-need-state')
        if cat=='COMMERCIAL':
            cand=f"Blue Cross Blue Shield ({title(st)})"
            return (cand,'family+cat+state') if cand in projset else (None,'bcbs-no-state-proj:'+title(st))
        if cat=='MEDICARE_ADVANTAGE':
            for c in [f"Blue Cross Blue Shield Medicare Advantage ({title(st)})"]:
                if c in projset: return (c,'family+cat+state')
            return (None,'bcbs-ma-need-review')
        if cat=='MEDICAID':
            for c in [f"Blue Cross Blue Shield Medicaid MCO ({title(st)})"]:
                if c in projset: return (c,'family+cat+state')
            return (None,'bcbs-medicaid-need-review')
        return (None,'bcbs-other')
    # 4. Medicaid family -> state FFS
    if fam=='Medicaid':
        st=parse_state(payer,orn)
        if not st: return (None,'medicaid-need-state')
        cand=f"Medicaid {title(st)}"
        return (cand,'family+state') if cand in projset else (None,'medicaid-no-state-proj:'+title(st))
    # 5. catch-all families need the specific payer
    return (None,'need-specific-payer')
