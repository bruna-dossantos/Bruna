#!/usr/bin/env python3
"""Family-anchored payer -> Linear project resolver (state/LOB aware). No hardcoded paths."""
import re

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

# national families: family + category -> single project (state-independent)
NAT={
 'Aetna':{'COMMERCIAL':'Aetna','MEDICARE_ADVANTAGE':'Aetna Medicare Advantage'},
 'Cigna':{'COMMERCIAL':'Cigna'},
 'Humana':{'COMMERCIAL':'Humana','MEDICARE_ADVANTAGE':'Humana Medicare Advantage'},
 'United HealthCare (UHC)':{'COMMERCIAL':'United Healthcare Commercial','MEDICARE_ADVANTAGE':'United Healthcare Medicare Advantage'},
 'Molina Healthcare':{'COMMERCIAL':'Molina Healthcare','MEDICARE_ADVANTAGE':'Molina Medicare Advantage'},
 'Oscar Health':{'COMMERCIAL':'Oscar'},
 'Kaiser Permanente':{'COMMERCIAL':'KAISER PERMANENTE'},
}

def resolve_family(fam, cat, payer, orn, projset):
    """Layer 2/3: family+category(+state). Returns (project_name|None, basis)."""
    fam=(fam or '').strip(); cat=(cat or '').strip()
    if cat=='MEDICARE':
        return ('Medicare','family+cat')
    if fam in NAT and cat in NAT[fam]:
        p=NAT[fam][cat]
        return (p,'family+cat') if p in projset else (None,'target-missing:'+p)
    if fam=='Blue Cross Blue Shield':
        st=parse_state(payer,orn)
        if not st:
            if not (payer or '').strip():
                if cat=='COMMERCIAL' and 'Anthem Blue Cross Blue Shield' in projset:
                    return ('Anthem Blue Cross Blue Shield','family:bcbs-blank->anthem')
                return (None,'bcbs-blank-noncommercial-review')
            return (None,'bcbs-need-state')
        if cat=='COMMERCIAL':
            cand=f"Blue Cross Blue Shield ({title(st)})"
            return (cand,'family+cat+state') if cand in projset else (None,'bcbs-no-state-proj:'+title(st))
        if cat=='MEDICARE_ADVANTAGE':
            cand=f"Blue Cross Blue Shield Medicare Advantage ({title(st)})"
            return (cand,'family+cat+state') if cand in projset else (None,'bcbs-ma-need-review')
        if cat=='MEDICAID':
            cand=f"Blue Cross Blue Shield Medicaid MCO ({title(st)})"
            return (cand,'family+cat+state') if cand in projset else (None,'bcbs-medicaid-need-review')
        return (None,'bcbs-other')
    if fam=='Medicaid':
        st=parse_state(payer,orn)
        if not st: return (None,'medicaid-need-state')
        cand=f"Medicaid {title(st)}"
        return (cand,'family+state') if cand in projset else (None,'medicaid-no-state-proj:'+title(st))
    return (None,'need-specific-payer')

# Layer 4: mine order_rule_name for brand+state+LOB.
# A template may be a list — the first candidate found in the projects list wins (handles brands
# whose project names vary, e.g. Humana "Health Horizons" in some states, "Healthy Horizons" in others).
BRAND=[
 (['fidelis'], "Fidelis Care"),
 (['nebraska total care'], "Nebraska Total Care Medicaid MCO (Nebraska)"),
 (['ambetter'], "Ambetter Centene Medicaid MCO ({S})"),
 (['centene'], "Centene Medicaid MCO ({S})"),
 (['northwood'], "Northwood"),
 (['humana healthy horizons','humana health horizons'],
   ["Humana Health Horizons Medicaid MCO ({S})","Humana Healthy Horizons Medicaid MCO ({S})"]),
 (['molina'], "Molina Medicaid MCO ({S})"),
 (['aetna better health'], "Aetna Better Health Medicaid MCO ({S})"),
 (['anthem'], "Anthem Medicaid MCO ({S})"),
 (['bcbs','blue cross'], "Blue Cross Blue Shield Medicaid MCO ({S})"),
 (['uhc','unitedhealthcare','united healthcare','community'], "United Healthcare Community Medicaid MCO ({S})"),
]
def resolve_ordername(orn, projset, slug2name, slug):
    n=(orn or '').lower()
    st=parse_state(orn)
    stt=title(st) if st else None
    for kws,tmpl in BRAND:
        if any(k in n for k in kws):
            tmpls=tmpl if isinstance(tmpl,list) else [tmpl]
            if any("{S}" in t for t in tmpls) and not stt: return (None,'ordername:brand-no-state')
            for t in tmpls:
                cand=t.replace("{S}",stt or "")
                if cand in projset: return (cand,'ordername')
                if slug(cand) in slug2name: return (slug2name[slug(cand)],'ordername')
            return (None,f'ordername:no-project:{tmpls[0].replace("{S}",stt or "")}')
    return (None,'ordername:no-indicator')

def lob_ok(cat, proj):
    """Reject a match whose line of business contradicts the row's plan_category."""
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
