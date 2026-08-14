#!/usr/bin/env python3
"""
render_criteria_explorer.py  —  pathway-first, click-to-policy criteria explorer

A criteria-first companion to the (rule-first) traceability HTML. Self-contained
(PDFs embedded, PDF.js from CDN). Right pane = every ORDER TYPE (pathway) as a
collapsible section listing its criteria; click a criterion and the left PDF pane
jumps to and highlights where that criterion came from in the policy.

Each criterion visibly separates two things (the confusing-when-blended part):
  • 📄 POLICY   — the requirement drawn from the policy (blue).
  • 🩺 CLINICAL  — how we pinned a vague term so it can be decided; our
                   interpretation, reviewer PENDING (amber).

The criterion→policy link comes from the traceability `became` map (criterion
identified by code + order_type + n) → the rule it became → that rule's location.

Usage:
  render_criteria_explorer.py criteria.json --traceability traceability.json \
      --locations rule_locations.json --pdf a.pdf b.pdf --title "..." --out explorer.html
"""

import sys
import json
import html
import base64
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import criterion_view as V  # noqa: E402


def build_reverse_index(trace):
    """Map criteria back to the rule(s) they came from, at three levels of specificity.

    The traceability `became` map records a match against ONE representative code,
    but identical criteria (same title) repeat across many codes and share the same
    policy origin. So we index by exact (code, order_type, n), by (order_type, title),
    and by title alone — and fall back through them so every code that carries a
    mapped criterion links to the same policy passage.
    """
    full, by_ot_title, by_title = {}, {}, {}
    for r in trace.get("rules", []):
        for b in (r.get("became") or []):
            hit = {"rule_id": r["id"], "match": b.get("match", 0),
                   "text": r.get("text", ""), "type": r.get("type", ""), "loc": r.get("loc")}
            title = (b.get("title", "") or "").strip().lower()
            full.setdefault((str(b.get("code")), b.get("order_type", ""), b.get("n")), []).append(hit)
            by_ot_title.setdefault((b.get("order_type", ""), title), []).append(hit)
            by_title.setdefault(title, []).append(hit)
    for d in (full, by_ot_title, by_title):
        for k in d:
            d[k].sort(key=lambda x: x["match"], reverse=True)
    return {"full": full, "ot_title": by_ot_title, "title": by_title}


def _lookup(code, ot_label, cr, idx):
    title = (cr.get("title", "") or "").strip().lower()
    return (idx["full"].get((str(code), ot_label, cr.get("n")))
            or idx["ot_title"].get((ot_label, title))
            or idx["title"].get(title) or [])


def criterion_payload(code, ot_label, cr, idx):
    policy, ods = V.split_criterion(cr)
    hits = _lookup(code, ot_label, cr, idx)
    locs = [{"source_pdf": h["loc"].get("source_pdf"), "page": h["loc"].get("page"),
             "rects": h["loc"].get("rects") or [h["loc"].get("bbox")],
             "rule_id": h["rule_id"], "match": h["match"], "text": h["text"][:400]}
            for h in hits if h.get("loc")]
    return {
        "n": cr.get("n"), "title": cr.get("title", ""), "type": cr.get("type", ""),
        "policy": policy, "source": cr.get("source", ""),
        "list_not_inlined": cr.get("list_not_inlined"),
        "op_defs": [{"term": od.get("term", ""), "reviewer": V.reviewer_status(od),
                     "lines": V.op_def_lines(od)} for od in ods],
        "locs": locs,
    }


def build_data(criteria, trace):
    idx = build_reverse_index(trace)
    groups = criteria.get("groups") or [{"group_label": None, "codes": criteria.get("codes", [])}]
    out_groups = []
    for g in groups:
        codes = []
        for c in g.get("codes", []):
            ots = c.get("order_types") or [{"order_type": c.get("description", "Standard"),
                                            "context": "", "logic_expression": None,
                                            "criteria": c.get("criteria", [])}]
            pathways = []
            for ot in ots:
                label = ot.get("order_type", "Qualification")
                crits = [criterion_payload(c["code"], label, cr, idx) for cr in ot.get("criteria", [])]
                mapped = sum(1 for cr in crits if cr["locs"])
                pathways.append({"order_type": label, "context": ot.get("context", ""),
                                 "logic_expression": ot.get("logic_expression"),
                                 "criteria": crits, "n_criteria": len(crits), "n_mapped": mapped})
            codes.append({"code": c["code"], "description": c.get("description", ""),
                          "modality": c.get("modality", ""), "contrast": c.get("contrast", ""),
                          "pathways": pathways})
        out_groups.append({"group_label": g.get("group_label"), "codes": codes})
    return {"policy": criteria.get("policy", {}), "groups": out_groups}


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — Pathways → Criteria → Policy</title>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1a1f29;--mut:#5b6472;--line:#e3e7ee;
        --pol:#2c5cc5;--polbg:#eaf0fc;--cli:#b7791f;--clibg:#fbf1de;
        --ok:#1a7f4b;--okbg:#e6f4ec;--warn:#c0392b;}
  *{box-sizing:border-box} body{margin:0;font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
  header{padding:12px 18px;background:var(--card);border-bottom:1px solid var(--line)}
  h1{margin:0 0 3px;font-size:17px} .sub{color:var(--mut);font-size:12px}
  .legend{display:flex;gap:14px;margin-top:8px;flex-wrap:wrap;font-size:12px;align-items:center}
  .lk{display:inline-flex;gap:6px;align-items:center}
  .sw{width:22px;height:14px;border-radius:3px;display:inline-block;border:1px solid var(--line)}
  .sw.pol{background:var(--polbg);border-left:4px solid var(--pol)} .sw.cli{background:var(--clibg);border-left:4px solid var(--cli)}
  .controls{display:flex;gap:8px;margin-top:9px;flex-wrap:wrap;align-items:center}
  input,button{padding:6px 10px;border:1px solid var(--line);border-radius:8px;font-size:13px;background:#fff}
  input[type=search]{flex:1;min-width:170px} button{cursor:pointer} button:hover{background:var(--bg)}
  .wrap{display:grid;grid-template-columns:1fr 1fr;height:calc(100vh - 150px)}
  .pane{overflow:auto;height:100%}
  .pdfpane{border-right:1px solid var(--line);background:#525659;display:flex;flex-direction:column}
  .pdfbar{display:flex;gap:8px;align-items:center;padding:8px 12px;background:#3a3d40;color:#e8e8e8;font-size:12px;flex-wrap:wrap}
  .pdfbar button{background:#5a5e62;color:#fff;border:0;border-radius:6px;padding:4px 9px}
  .pdfbar button:hover{background:#6a6f74}
  .cw{position:relative;margin:12px auto;box-shadow:0 2px 10px rgba(0,0,0,.4);background:#fff}
  .cw canvas{display:block} .hl{position:absolute;border-radius:2px;pointer-events:none}
  .hl.focus{background:rgba(255,214,0,.42);outline:2px solid #f5a623}
  .body{padding:12px 14px}
  .grouplbl{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin:14px 0 6px;font-weight:700}
  .code{margin-bottom:10px}
  .codehd{font-weight:700;font-size:14px;margin:10px 0 6px}
  .pathway{background:var(--card);border:1px solid var(--line);border-radius:10px;margin-bottom:10px;overflow:hidden}
  .pwhd{display:flex;gap:8px;align-items:center;padding:10px 12px;cursor:pointer;user-select:none;background:linear-gradient(0deg,#fbfcfe,#fff)}
  .pwhd:hover{background:var(--bg)}
  .tw{transition:transform .15s;color:var(--mut);font-size:12px} .pathway.open .tw{transform:rotate(90deg)}
  .pwname{font-weight:700;font-size:13.5px}
  .pill{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:20px;background:var(--okbg);color:var(--ok);border:1px solid var(--line)}
  .pill.part{background:#fbf1de;color:var(--cli)}
  .logic{font-size:11.5px;color:var(--mut);margin-left:auto;font-style:italic}
  .pwbody{display:none;padding:4px 12px 12px} .pathway.open .pwbody{display:block}
  .ctx{font-size:11.5px;color:var(--mut);margin:2px 0 8px}
  .crit{border:1px solid var(--line);border-radius:9px;margin:8px 0;overflow:hidden;cursor:pointer}
  .crit:hover{box-shadow:0 1px 8px rgba(0,0,0,.08)} .crit.sel{box-shadow:0 0 0 2px #f5a623}
  .crithd{display:flex;gap:8px;align-items:center;padding:8px 10px;background:var(--bg)}
  .cbadge{font-size:10px;font-weight:700;color:#fff;background:var(--mut);border-radius:6px;padding:2px 7px}
  .ctitle{font-weight:600;font-size:13px} .ctype{font-size:10px;color:var(--mut);text-transform:uppercase;letter-spacing:.03em}
  .jump{margin-left:auto;font-size:11px;color:var(--pol);font-weight:700;white-space:nowrap}
  .jump.no{color:var(--mut);font-weight:400;font-style:italic}
  .block{padding:8px 10px;border-left:4px solid var(--line);margin:8px 10px}
  .block.pol{background:var(--polbg);border-left-color:var(--pol)}
  .block.cli{background:var(--clibg);border-left-color:var(--cli);margin-top:6px}
  .blbl{font-size:10px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;margin-bottom:3px}
  .block.pol .blbl{color:var(--pol)} .block.cli .blbl{color:var(--cli)}
  .ptext{font-size:12.7px;white-space:pre-wrap}
  .src{font-size:11px;color:var(--mut);font-style:italic;margin-top:5px}
  .callout{font-size:11.5px;color:var(--warn);margin-top:5px;font-weight:600}
  .odterm{font-weight:700;font-size:12px} .odrev{font-size:10px;font-weight:700;color:#fff;background:var(--cli);border-radius:5px;padding:1px 6px;margin-left:6px}
  .odrow{font-size:12px;margin:2px 0} .odrow b{color:var(--cli)}
  .none{color:var(--mut);font-size:12px;font-style:italic;padding:4px 10px}
  @media(max-width:900px){.wrap{grid-template-columns:1fr;height:auto}.pdfpane{height:65vh}}
</style></head>
<body>
<header>
  <h1>__TITLE__ <span class="sub">· pathways → criteria → policy</span></h1>
  <div class="sub">Expand a pathway, then click a criterion to jump to exactly where it came from in the policy (highlighted on the left).</div>
  <div class="legend">
    <span class="lk"><span class="sw pol"></span> 📄 <b>Policy</b> — the requirement, from the policy source</span>
    <span class="lk"><span class="sw cli"></span> 🩺 <b>Clinical interpretation</b> — how we pinned a vague term (reviewer PENDING)</span>
  </div>
  <div class="controls">
    <input type="search" id="q" placeholder="Filter criteria / pathways…">
    <button id="expand">Expand all</button><button id="collapse">Collapse all</button>
  </div>
</header>
<div class="wrap">
  <div class="pane pdfpane">
    <div class="pdfbar">
      <select id="pdfpick"></select>
      <button id="prev">‹ Prev</button><span id="pglabel">—</span><button id="next">Next ›</button>
      <span style="margin-left:auto;color:#b9bdc2" id="hint">click a criterion →</span>
    </div>
    <div id="scroll" style="flex:1;overflow:auto;width:100%"></div>
  </div>
  <div class="pane body" id="tree"></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js"></script>
<script>
const DATA=__DATA__, PDFS=__PDFS__;
pdfjsLib.GlobalWorkerOptions.workerSrc="https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js";
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function b64u(b64){const bin=atob(b64);const a=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);return a}
const cache={}; let cur={pdf:null,page:1};
async function getDoc(n){if(!cache[n])cache[n]=await pdfjsLib.getDocument({data:b64u(PDFS[n])}).promise;return cache[n]}
function fitScale(page){const w=document.getElementById('scroll').clientWidth-24;const base=page.getViewport({scale:1});return Math.min(2.0,Math.max(0.6,w/base.width))}
async function renderPageCanvas(doc,pageNum,scale){
  const page=await doc.getPage(pageNum);const vp=page.getViewport({scale});
  const cw=document.createElement('div');cw.className='cw';cw.style.width=vp.width+'px';
  const cv=document.createElement('canvas');cv.width=vp.width;cv.height=vp.height;cw.appendChild(cv);
  await page.render({canvasContext:cv.getContext('2d'),viewport:vp}).promise; return {cw,scale,vp};
}
function addRect(cw,rect,scale,cls){
  const d=document.createElement('div');d.className='hl '+cls;
  d.style.left=rect[0]*scale+'px';d.style.top=rect[1]*scale+'px';
  d.style.width=Math.max(4,(rect[2]-rect[0])*scale)+'px';d.style.height=Math.max(8,(rect[3]-rect[1])*scale)+'px';
  cw.appendChild(d); return d;
}
async function showSingle(name,pageNum,rects){
  const scroll=document.getElementById('scroll');scroll.innerHTML='';
  const doc=await getDoc(name); pageNum=Math.max(1,Math.min(pageNum,doc.numPages)); cur={pdf:name,page:pageNum};
  const {cw,scale}=await renderPageCanvas(doc,pageNum,fitScale(await doc.getPage(pageNum)));
  scroll.appendChild(cw); document.getElementById('pdfpick').value=name;
  document.getElementById('pglabel').textContent='p.'+pageNum+' / '+doc.numPages;
  let first=null;(rects||[]).forEach(r=>{const d=addRect(cw,r,scale,'focus');if(!first)first=d});
  if(first)scroll.scrollTo({top:Math.max(0,parseFloat(first.style.top)-120),behavior:'smooth'});
}
document.getElementById('prev').onclick=()=>showSingle(cur.pdf,cur.page-1,null);
document.getElementById('next').onclick=()=>showSingle(cur.pdf,cur.page+1,null);
document.getElementById('pdfpick').onchange=e=>showSingle(e.target.value,1,null);

function odBlock(od){
  const rows=od.lines.map(([k,v])=>`<div class="odrow"><b>${esc(k)}:</b> ${esc(v)}</div>`).join('');
  return `<div class="block cli"><div class="blbl">🩺 Clinical interpretation</div>
    <span class="odterm">"${esc(od.term)}"</span><span class="odrev">reviewer ${esc(od.reviewer)}</span>${rows}</div>`;
}
function critCard(code,otLabel,cr){
  const loc=cr.locs&&cr.locs[0];
  const jump=loc?`<span class="jump">↦ show in policy · ${esc(loc.source_pdf)} p${loc.page}</span>`
                :`<span class="jump no">no mapped policy location</span>`;
  const pol=cr.policy?`<div class="block pol"><div class="blbl">📄 Policy — the requirement</div>
      <div class="ptext">${esc(cr.policy)}</div>`
      +(cr.list_not_inlined?`<div class="callout">⚠ ${esc(cr.list_not_inlined.what)}: ${cr.list_not_inlined.count.toLocaleString()} codes — see ${esc(cr.list_not_inlined.location)}</div>`:``)
      +(cr.source?`<div class="src">Source: ${esc(cr.source)}</div>`:``)+`</div>`:``;
  const cli=cr.op_defs.map(odBlock).join('');
  return `<div class="crit" data-loc='${loc?esc(JSON.stringify(loc)):""}'>
    <div class="crithd"><span class="cbadge">${cr.n}</span><span class="ctitle">${esc(cr.title)}</span>
      <span class="ctype">${esc(cr.type)}</span>${jump}</div>${pol}${cli}</div>`;
}
function pathwayEl(code,pw){
  const pill=pw.n_mapped===pw.n_criteria?`<span class="pill">${pw.n_criteria} criteria · all mapped</span>`
            :`<span class="pill part">${pw.n_mapped}/${pw.n_criteria} mapped to policy</span>`;
  const logic=pw.logic_expression?`<span class="logic">qualifies when: ${esc(pw.logic_expression)}</span>`:``;
  const ctx=pw.context?`<div class="ctx">${esc(pw.context)}</div>`:``;
  const crits=pw.criteria.map(cr=>critCard(code,pw.order_type,cr)).join('');
  return `<div class="pathway open">
    <div class="pwhd"><span class="tw">▶</span><span class="pwname">${esc(pw.order_type)}</span>${pill}${logic}</div>
    <div class="pwbody">${ctx}${crits||'<div class="none">No criteria.</div>'}</div></div>`;
}
function build(){
  const t=document.getElementById('tree'); t.innerHTML='';
  DATA.groups.forEach(g=>{
    if(g.group_label)t.insertAdjacentHTML('beforeend',`<div class="grouplbl">${esc(g.group_label)}</div>`);
    g.codes.forEach(c=>{
      let h=`<div class="code"><div class="codehd">${esc(c.code)} — ${esc(c.description)}`+
        (c.modality?` · ${esc(c.modality)}`:``)+(c.contrast?` · ${esc(c.contrast)}`:``)+`</div>`;
      h+=c.pathways.map(pw=>pathwayEl(c.code,pw)).join('');
      h+=`</div>`; t.insertAdjacentHTML('beforeend',h);
    });
  });
  // wire pathway toggles
  t.querySelectorAll('.pwhd').forEach(hd=>hd.onclick=()=>hd.parentElement.classList.toggle('open'));
  // wire criterion click → jump
  t.querySelectorAll('.crit').forEach(el=>el.onclick=ev=>{
    ev.stopPropagation();
    t.querySelectorAll('.crit.sel').forEach(x=>x.classList.remove('sel')); el.classList.add('sel');
    const raw=el.getAttribute('data-loc'); if(!raw)return;
    const loc=JSON.parse(raw); showSingle(loc.source_pdf,loc.page,loc.rects);
    document.getElementById('hint').textContent=loc.rule_id+' · match '+Math.round(loc.match*100)+'%';
  });
}
document.getElementById('expand').onclick=()=>document.querySelectorAll('.pathway').forEach(p=>p.classList.add('open'));
document.getElementById('collapse').onclick=()=>document.querySelectorAll('.pathway').forEach(p=>p.classList.remove('open'));
document.getElementById('q').addEventListener('input',e=>{
  const q=e.target.value.toLowerCase();
  document.querySelectorAll('.pathway').forEach(pw=>{
    let any=false;
    pw.querySelectorAll('.crit').forEach(cr=>{const m=!q||cr.textContent.toLowerCase().includes(q);cr.style.display=m?'':'none';if(m)any=true});
    const nameM=pw.querySelector('.pwname').textContent.toLowerCase().includes(q);
    pw.style.display=(any||nameM||!q)?'':'none'; if(q&&(any))pw.classList.add('open');
  });
});
const pick=document.getElementById('pdfpick');Object.keys(PDFS).forEach(n=>{const o=document.createElement('option');o.value=n;o.textContent=n;pick.appendChild(o)});
build();
showSingle(Object.keys(PDFS)[0],1,null);
</script></body></html>"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pathway-first click-to-policy criteria explorer")
    ap.add_argument("criteria_json")
    ap.add_argument("--traceability", required=True)
    ap.add_argument("--locations", required=True)
    ap.add_argument("--pdf", nargs="+", required=True)
    ap.add_argument("--title", default="Criteria")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    criteria = json.loads(Path(args.criteria_json).read_text())
    trace = json.loads(Path(args.traceability).read_text())
    locs = json.loads(Path(args.locations).read_text())
    for r in trace.get("rules", []):
        r["loc"] = locs.get(r["id"])
    data = build_data(criteria, trace)
    pdfs = {Path(p).name: base64.b64encode(Path(p).read_bytes()).decode() for p in args.pdf}
    page = (PAGE.replace("__TITLE__", html.escape(args.title))
                .replace("__DATA__", json.dumps(data)).replace("__PDFS__", json.dumps(pdfs)))
    Path(args.out).write_text(page)
    n_crit = sum(len(pw["criteria"]) for g in data["groups"] for c in g["codes"] for pw in c["pathways"])
    n_map = sum(1 for g in data["groups"] for c in g["codes"] for pw in c["pathways"]
                for cr in pw["criteria"] if cr["locs"])
    print(f"wrote {args.out} ({n_crit} criteria, {n_map} mapped to policy, {len(pdfs)} PDFs, "
          f"{len(page)//1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
