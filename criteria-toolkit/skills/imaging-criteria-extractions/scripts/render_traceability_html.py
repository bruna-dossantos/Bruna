#!/usr/bin/env python3
"""
render_traceability_html.py  —  interactive policy → rules → criteria explorer

Self-contained HTML (PDFs embedded, PDF.js). Two viewing modes:
  - Click a rule → the viewer jumps to its page and highlights the exact passage
    (sharp per-line boxes from locate_rules_in_pdf.py).
  - "Overlay all" → renders every page of the chosen PDF with ALL rules drawn at
    once, color-coded by type (indication / exclusion / limitation / administrative),
    so un-annotated policy text stands out — what the extractor missed.

Usage:
  render_traceability_html.py traceability.json --locations rule_locations.json \
      --pdf a.pdf b.pdf --title "..." --out traceability.html
"""

import sys
import json
import html
import base64
import argparse
from pathlib import Path

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — Policy → Rules → Criteria</title>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1a1f29;--mut:#5b6472;--line:#e3e7ee;
        --cov:#1a7f4b;--covbg:#e6f4ec;--par:#b7791f;--parbg:#fbf1de;--gap:#c0392b;--gapbg:#fbe9e7;
        --ind:#2c5cc5;--exc:#8e44ad;--lim:#0e7490;--adm:#7a8290;}
  *{box-sizing:border-box} body{margin:0;font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
  header{padding:12px 18px;background:var(--card);border-bottom:1px solid var(--line)}
  h1{margin:0 0 3px;font-size:17px} .sub{color:var(--mut);font-size:12px}
  .chips{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;align-items:center}
  .chip{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;border:1px solid var(--line)}
  .chip.cov{color:var(--cov);background:var(--covbg)} .chip.par{color:var(--par);background:var(--parbg)} .chip.gap{color:var(--gap);background:var(--gapbg)}
  .controls{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
  input,select{padding:6px 9px;border:1px solid var(--line);border-radius:8px;font-size:13px;background:#fff}
  input[type=search]{flex:1;min-width:150px}
  .wrap{display:grid;grid-template-columns:1fr 1fr;height:calc(100vh - 118px)}
  .pane{overflow:auto;height:100%}
  .pdfpane{border-right:1px solid var(--line);background:#525659;display:flex;flex-direction:column}
  .pdfbar{display:flex;gap:8px;align-items:center;padding:8px 12px;background:#3a3d40;color:#e8e8e8;font-size:12px;flex-wrap:wrap}
  .pdfbar button{background:#5a5e62;color:#fff;border:0;border-radius:6px;padding:4px 9px;cursor:pointer}
  .pdfbar button:hover{background:#6a6f74} .pdfbar select{padding:3px 6px;font-size:12px}
  .pdfbar label{display:flex;gap:4px;align-items:center;cursor:pointer}
  .legend{display:flex;gap:10px;align-items:center;padding:5px 12px;background:#43474a;color:#ddd;font-size:11px}
  .legend .lk{display:inline-flex;gap:5px;align-items:center} .legend .sw{width:12px;height:12px;border-radius:3px;display:inline-block}
  .cw{position:relative;margin:12px auto;box-shadow:0 2px 10px rgba(0,0,0,.4);background:#fff}
  .cw canvas{display:block}
  .hl{position:absolute;border-radius:2px;pointer-events:none}
  .hl.focus{background:rgba(255,214,0,.42);outline:2px solid #f5a623}
  .hl.ov{cursor:pointer;pointer-events:auto}
  .rules{padding:12px 14px}
  .rule{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:10px;padding:9px 11px;margin-bottom:9px;cursor:pointer}
  .rule:hover{box-shadow:0 1px 6px rgba(0,0,0,.06)} .rule.sel{box-shadow:0 0 0 2px #f5a623}
  .rule.cov{border-left-color:var(--cov)} .rule.par{border-left-color:var(--par)} .rule.gap{border-left-color:var(--gap)}
  .rhead{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
  .badge{font-size:10px;font-weight:700;padding:2px 7px;border-radius:6px}
  .b-cov{color:#fff;background:var(--cov)} .b-par{color:#fff;background:var(--par)} .b-gap{color:#fff;background:var(--gap)}
  .b-INDICATION{color:#fff;background:var(--ind)} .b-EXCLUSION{color:#fff;background:var(--exc)}
  .b-LIMITATION{color:#fff;background:var(--lim)} .b-ADMINISTRATIVE{color:#fff;background:var(--adm)}
  .rid{font-weight:700;color:var(--mut);font-size:12px} .orflag{font-size:10px;color:var(--par);font-weight:700}
  .loc{font-size:10.5px;color:var(--mut);margin-left:auto}
  .rtext{margin:6px 0 0;font-size:13px}
  .detail{margin-top:9px;border-top:1px dashed var(--line);padding-top:9px;display:none} .rule.open .detail{display:block}
  .miss{font-size:12px;color:var(--gap);margin:4px 0}
  .became h4{margin:6px 0 4px;font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
  .crit{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:7px 9px;margin:6px 0}
  .crit .cm{font-size:11px;color:var(--mut)} .crit .ct{font-weight:600;font-size:13px}
  .crit .cd{font-size:12.5px;margin-top:3px} .crit .cs{font-size:11px;color:var(--mut);font-style:italic;margin-top:4px}
  .none{color:var(--gap);font-size:12.5px;font-style:italic}
  @media(max-width:900px){.wrap{grid-template-columns:1fr;height:auto}.pdfpane{height:70vh}}
</style></head>
<body>
<header>
  <h1>__TITLE__</h1>
  <div class="sub">Click a rule → jump to and highlight where it appears in the policy. Or turn on <b>Overlay all</b> to see every captured rule at once, color-coded by type. White = non-rule text (background, definitions, billing, the ICD code table) — a policy is mostly prose around a few decisive rules, so white is expected, not a gap.</div>
  <div class="chips" id="chips"></div>
  <div class="controls">
    <input type="search" id="q" placeholder="Search rule text…">
    <select id="ftype"><option value="">All types</option><option>INDICATION</option><option>EXCLUSION</option><option>LIMITATION</option><option>ADMINISTRATIVE</option></select>
    <select id="fstatus"><option value="">All statuses</option><option value="covered">Covered</option><option value="partial">Partial</option><option value="gap">Gap</option></select>
    <label style="font-size:12px;color:var(--mut)"><input type="checkbox" id="showall"> show admin / out-of-scope</label>
  </div>
</header>
<div class="wrap">
  <div class="pane pdfpane">
    <div class="pdfbar">
      <select id="pdfpick"></select>
      <label><input type="checkbox" id="overlay"> Overlay all</label>
      <button id="prev">‹ Prev</button><span id="pglabel">—</span><button id="next">Next ›</button>
      <span style="margin-left:auto;color:#b9bdc2" id="hint"></span>
    </div>
    <div class="legend" id="legend" style="display:none">
      <span>Rule type:</span>
      <span class="lk"><span class="sw" style="background:var(--ind)"></span>Indication</span>
      <span class="lk"><span class="sw" style="background:var(--exc)"></span>Exclusion</span>
      <span class="lk"><span class="sw" style="background:var(--lim)"></span>Limitation</span>
      <span class="lk"><span class="sw" style="background:var(--adm)"></span>Administrative</span>
      <span style="margin-left:auto;color:#b9bdc2">white = non-rule text (background · definitions · billing · code tables), not a gap</span>
    </div>
    <div id="scroll" style="flex:1;overflow:auto;width:100%"></div>
  </div>
  <div class="pane rules" id="rules"></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js"></script>
<script>
const DATA=__DATA__, PDFS=__PDFS__;
pdfjsLib.GlobalWorkerOptions.workerSrc="https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js";
const S={covered:'cov',partial:'par',gap:'gap'};
const TC={INDICATION:'44,92,197',EXCLUSION:'142,68,173',LIMITATION:'14,116,144',ADMINISTRATIVE:'122,130,144'};
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function b64u(b64){const bin=atob(b64);const a=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);return a}
const cache={}; let cur={pdf:null,page:1};
async function getDoc(n){if(!cache[n])cache[n]=await pdfjsLib.getDocument({data:b64u(PDFS[n])}).promise;return cache[n]}
function fitScale(page){const w=document.getElementById('scroll').clientWidth-24;const base=page.getViewport({scale:1});return Math.min(2.0,Math.max(0.6,w/base.width))}
async function renderPageCanvas(doc,pageNum,scale){
  const page=await doc.getPage(pageNum);const vp=page.getViewport({scale});
  const cw=document.createElement('div');cw.className='cw';cw.style.width=vp.width+'px';
  const cv=document.createElement('canvas');cv.width=vp.width;cv.height=vp.height;cw.appendChild(cv);
  await page.render({canvasContext:cv.getContext('2d'),viewport:vp}).promise;
  return {cw,scale,vp};
}
function addRect(cw,rect,scale,cls,style,title){
  const d=document.createElement('div');d.className='hl '+cls;
  d.style.left=rect[0]*scale+'px';d.style.top=rect[1]*scale+'px';
  d.style.width=Math.max(4,(rect[2]-rect[0])*scale)+'px';d.style.height=Math.max(8,(rect[3]-rect[1])*scale)+'px';
  if(style)Object.assign(d.style,style); if(title)d.title=title; cw.appendChild(d); return d;
}
async function showSingle(name,pageNum,rects){
  document.getElementById('overlay').checked=false; document.getElementById('legend').style.display='none';
  const scroll=document.getElementById('scroll');scroll.innerHTML='';
  const doc=await getDoc(name); pageNum=Math.max(1,Math.min(pageNum,doc.numPages)); cur={pdf:name,page:pageNum};
  const {cw,scale}=await renderPageCanvas(doc,pageNum,fitScale(await doc.getPage(pageNum)));
  scroll.appendChild(cw);
  document.getElementById('pdfpick').value=name;
  document.getElementById('pglabel').textContent='p.'+pageNum+' / '+doc.numPages;
  let first=null;
  (rects||[]).forEach(r=>{const d=addRect(cw,r,scale,'focus');if(!first)first=d});
  document.getElementById('hint').textContent=rects&&rects.length?'highlighted':'';
  if(first)scroll.scrollTo({top:Math.max(0,parseFloat(first.style.top)-120),behavior:'smooth'});
}
async function overlayAll(name){
  document.getElementById('legend').style.display='flex';
  const scroll=document.getElementById('scroll');scroll.innerHTML='';cur={pdf:name,page:1};
  document.getElementById('pdfpick').value=name; document.getElementById('pglabel').textContent='all pages';
  document.getElementById('hint').textContent='every rule shown';
  const doc=await getDoc(name);
  const showall=document.getElementById('showall').checked;
  const byPage={}; DATA.rules.forEach(r=>{if(r.loc&&r.loc.source_pdf===name&&(showall||(r.relevance||'clinical')==='clinical')){(byPage[r.loc.page]=byPage[r.loc.page]||[]).push(r)}});
  let shown=0;
  for(let p=1;p<=doc.numPages;p++){
    const {cw,scale}=await renderPageCanvas(doc,p,fitScale(await doc.getPage(p)));
    scroll.appendChild(cw);
    (byPage[p]||[]).forEach(r=>{const c=TC[r.type]||'122,130,144';
      // shade the rule's WHOLE footprint (first→last matched line), not just one phrase,
      // so a captured rule reads as a block. Left/right padded to the text column.
      const rects=r.loc.rects||[r.loc.bbox];
      const x0=Math.min(...rects.map(x=>x[0])), top=Math.min(...rects.map(x=>x[1]));
      const x1=Math.max(...rects.map(x=>x[2])), bot=Math.max(...rects.map(x=>x[3]));
      addRect(cw,[x0,top,x1,bot],scale,'ov',
        {background:'rgba('+c+',.22)',outline:'1.5px solid rgb('+c+')'},
        r.id+' · '+r.type+' · '+r.text.slice(0,90)).onclick=()=>selectRule(r.id,false);
      shown++;
    });
  }
  document.getElementById('hint').textContent=shown+' rules shaded · white = non-rule text (background, definitions, billing, code tables)';
}
document.getElementById('prev').onclick=()=>{if(!document.getElementById('overlay').checked)showSingle(cur.pdf,cur.page-1,null)};
document.getElementById('next').onclick=()=>{if(!document.getElementById('overlay').checked)showSingle(cur.pdf,cur.page+1,null)};
document.getElementById('overlay').onchange=e=>{if(e.target.checked)overlayAll(document.getElementById('pdfpick').value);else showSingle(document.getElementById('pdfpick').value,1,null)};
document.getElementById('pdfpick').onchange=e=>{if(document.getElementById('overlay').checked)overlayAll(e.target.value);else showSingle(e.target.value,1,null)};
function chips(rows,hidden){const c={covered:0,partial:0,gap:0};rows.forEach(r=>c[r.status]++);
  const h=hidden?`<span class="sub">· ${hidden} admin / out-of-scope hidden</span>`:'';
  document.getElementById('chips').innerHTML=`<span class="chip cov">${c.covered} covered</span><span class="chip par">${c.partial} partial</span><span class="chip gap">${c.gap} gap</span><span class="sub">of ${rows.length} clinical rules</span>${h}`}
function card(r){
  const loc=r.loc?`<span class="loc">${esc(r.loc.source_pdf)} · p${r.loc.page}${r.loc.sharp?'':' ~'}</span>`:`<span class="loc">no location</span>`;
  const became=r.became&&r.became.length?`<div class="became"><h4>Became criteria</h4>`+r.became.map(c=>
      `<div class="crit"><div class="cm">${esc(c.code)} · ${esc(c.order_type)} · C${c.n} · ${esc(c.type)} · match ${Math.round(c.match*100)}%</div><div class="ct">${esc(c.title)}</div><div class="cd">${esc(c.definition).slice(0,320)}</div>`+(c.source?`<div class="cs">Source: ${esc(c.source)}</div>`:``)+`</div>`).join('')+`</div>`
    :`<div class="none">No criterion clearly maps here — review whether it should (or is an administrative / general-guideline line that legitimately has no criterion).</div>`;
  const miss=r.missing_terms&&r.missing_terms.length?`<div class="miss">Missing terms: ${esc(r.missing_terms.join(', '))}</div>`:``;
  return `<div class="rule ${S[r.status]}" data-id="${r.id}">
    <div class="rhead"><span class="rid">${r.id}</span><span class="badge b-${r.type}">${r.type}</span>
      <span class="badge b-${S[r.status]}">${r.status.toUpperCase()}</span>
      ${r.relevance&&r.relevance!=='clinical'?`<span class="badge" style="background:var(--adm);color:#fff">${r.relevance.replace('_',' ')}</span>`:''}
      ${r.has_or_group?'<span class="orflag">[or-group]</span>':''}${loc}</div>
    <div class="rtext">${esc(r.text)}</div><div class="detail">${miss}${became}</div></div>`;
}
function selectRule(id,toggle){
  const r=DATA.rules.find(x=>x.id===id); if(!r)return;
  document.querySelectorAll('.rule.sel').forEach(x=>x.classList.remove('sel'));
  const el=document.querySelector('.rule[data-id="'+id+'"]');
  if(el){el.classList.add('sel'); if(toggle)el.classList.toggle('open'); else el.classList.add('open'); el.scrollIntoView({block:'nearest',behavior:'smooth'});}
  if(r.loc)showSingle(r.loc.source_pdf,r.loc.page,r.loc.rects||[r.loc.bbox]);
}
function render(){
  const q=document.getElementById('q').value.toLowerCase(),ft=document.getElementById('ftype').value,
        fs=document.getElementById('fstatus').value,showall=document.getElementById('showall').checked;
  const relOK=r=>showall||(r.relevance||'clinical')==='clinical';
  const rows=DATA.rules.filter(r=>relOK(r)&&(!ft||r.type===ft)&&(!fs||r.status===fs)&&(!q||r.text.toLowerCase().includes(q)));
  const hidden=showall?0:DATA.rules.filter(r=>(r.relevance||'clinical')!=='clinical').length;
  chips(rows,hidden);
  document.getElementById('rules').innerHTML=rows.map(card).join('')||'<p class="none">No rules match.</p>';
  document.querySelectorAll('.rule').forEach(el=>el.onclick=()=>selectRule(el.dataset.id,true));
}
['q','ftype','fstatus'].forEach(id=>document.getElementById(id).addEventListener('input',render));
document.getElementById('showall').addEventListener('change',()=>{render(); if(document.getElementById('overlay').checked) overlayAll(document.getElementById('pdfpick').value);});
const pick=document.getElementById('pdfpick');Object.keys(PDFS).forEach(n=>{const o=document.createElement('option');o.value=n;o.textContent=n;pick.appendChild(o)});
render();
showSingle(Object.keys(PDFS)[0],1,null);
</script></body></html>"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Interactive traceability HTML")
    ap.add_argument("traceability_json")
    ap.add_argument("--locations", required=True)
    ap.add_argument("--pdf", nargs="+", required=True)
    ap.add_argument("--title", default="Policy")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    data = json.loads(Path(args.traceability_json).read_text())
    locs = json.loads(Path(args.locations).read_text())
    for r in data["rules"]:
        r["loc"] = locs.get(r["id"])
    pdfs = {Path(p).name: base64.b64encode(Path(p).read_bytes()).decode() for p in args.pdf}
    page = (PAGE.replace("__TITLE__", html.escape(args.title))
                .replace("__DATA__", json.dumps(data)).replace("__PDFS__", json.dumps(pdfs)))
    Path(args.out).write_text(page)
    print(f"wrote {args.out} ({len(data['rules'])} rules, {len(pdfs)} PDFs, {len(page)//1024} KB)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
