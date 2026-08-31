/* Evidence graphics are rendered from verified response fields, never AI-generated numbers. */
(() => {
  const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
  const download=(content,type,name)=>{const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
  const value=m=>typeof m.value==='number'?m.value.toLocaleString('en-US',{maximumFractionDigits:3}):String(m.value??'Not available');
  function markdown(b){
    return ['# '+b.title,'Generated: '+b.generated_at,'Audience: '+b.audience,'Question: '+b.question,'## Evidence summary',b.summary,
      '## Key figures',...b.metrics.map(m=>'- '+m.label+': '+value(m)+' '+m.unit),
      ...b.timeline.flatMap(t=>['## '+t.title,t.text]),...(b.sections||[]).flatMap(t=>['## '+t.title,t.kind,t.text,t.source_url||'']),...(b.what_changed?['## What changed',b.what_changed]:[]),
      '## Limitations',...b.limitations.map(t=>'- '+t),'## Sources',...b.sources.map(s=>'- '+s.organization+'. '+s.title+'. Reporting through '+(s.reporting_cutoff||'not stated')+'. Published '+(s.published||'not stated')+'. Retrieved '+(s.retrieved_at||'not stated')+'. '+s.url),
      '## Evidence IDs',...b.evidence_ids,'## Method',b.method].join('\n\n');
  }
  function infographic(b){
    let y=70;const parts=[];
    const line=(text,size=20,color='#163d31',bold=false)=>{parts.push('<text x="55" y="'+y+'" font-size="'+size+'" fill="'+color+'"'+(bold?' font-weight="700"':'')+'>'+esc(text)+'</text>');y+=size+13};
    const paragraph=(text,size=20)=>{const chunks=String(text).split(/\s+/).flatMap(w=>w.match(/.{1,82}/g)||[]);let row='';for(const w of chunks){if((row+' '+w).length>88){line(row,size);row=w}else row+=(row?' ':'')+w}if(row)line(row,size);y+=12};
    line('FYNURA  /  EVIDENCE BRIEF',30,'#087858',true);paragraph(b.title,26);
    line('Audience: '+b.audience,17);line('Generated: '+b.generated_at,16);y+=15;
    for(const m of b.metrics){parts.push('<rect x="40" y="'+(y-25)+'" width="1120" height="104" rx="14" fill="#e6f2e9"/>');line(value(m)+' '+m.unit,28,'#087858',true);paragraph(m.label,17);y+=15}
    if(b.ranking?.length){line('REPORTED BURDEN / COMPARABLE COUNTRY REPORTS',18,'#087858',true);const max=Math.max(...b.ranking.map(r=>r.value),1);for(const r of b.ranking){line(r.label+' · '+Number(r.value).toLocaleString()+' '+r.unit,20);parts.push('<rect x="55" y="'+y+'" width="'+(1050*r.value/max)+'" height="18" rx="4" fill="#148362"/>');y+=45}paragraph('Selected comparable stored reports, not population-adjusted risk. See geographic interpretation and source below.',16)}
    if(b.actions?.length){line('WHO CONTROL PRIORITIES / GENERAL GUIDANCE',18,'#087858',true);for(const [i,a] of b.actions.entries()){const top=y;parts.push('<rect x="40" y="'+(top-23)+'" width="1120" height="132" rx="14" fill="'+(i%2?'#e8f0f8':'#e5f3ed')+'"/>');line(String(i+1).padStart(2,'0')+'   '+a.title,25,'#087858',true);paragraph(a.text,19);y=Math.max(y,top+125)}y+=12}
    line('WHAT THE EVIDENCE SUPPORTS',18,'#087858',true);paragraph(b.summary);
    for(const s of b.sections||[]){line(s.title.toUpperCase(),18,'#087858',true);paragraph(s.kind,15);paragraph(s.text);if(s.source_url)paragraph(s.source_url,14)}
    for(const t of b.timeline){line(t.title.toUpperCase(),18,'#087858',true);paragraph(t.text)}
    if(b.what_changed){line('WHAT CHANGED',18,'#087858',true);paragraph(b.what_changed)}
    line('READ BEFORE SHARING',18,'#9a531e',true);for(const t of b.limitations)paragraph(t,17);
    line('SOURCE PROVENANCE',18,'#087858',true);for(const s of b.sources){paragraph(s.organization+' · '+s.title+' · Reporting through '+(s.reporting_cutoff||'not stated'),17);paragraph(s.url,15)}
    paragraph('See the accompanying report brief for retrieval dates and every contributing evidence ID. '+b.method,15);
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="'+(y+35)+'" viewBox="0 0 1200 '+(y+35)+'" role="img" aria-label="'+esc(b.title)+'"><title>'+esc(b.title)+'</title><metadata>'+esc(JSON.stringify({evidence_ids:b.evidence_ids,sources:b.sources,generated_at:b.generated_at}))+'</metadata><rect width="100%" height="100%" fill="#f8fbf7"/><g font-family="Arial, sans-serif">'+parts.join('')+'</g></svg>';
  }
  window.appendBrief=(parent,b)=>{
    if(!parent)return;
    const panel=document.createElement('article');panel.className='generated-brief';
    panel.innerHTML='<h3>Report brief and infographic ready</h3><p>'+esc(b.scope.geography||'Selected scope')+' · '+esc(b.audience)+'</p><div class="brief-actions"><button data-brief-md>Download report brief (.md)</button><button data-brief-svg>Download infographic (SVG)</button><button data-brief-png>Download infographic (PNG)</button></div><p role="status" class="brief-status">Includes citations, reporting dates and limitations. Review before publication.</p><details><summary>Preview evidence infographic</summary><div class="brief-preview"></div></details>';
    parent.append(panel);const narrative=document.createElement('div');narrative.className='brief-insights';narrative.innerHTML=(b.sections||[]).map(s=>'<section><h4>'+esc(s.title)+'</h4><small>'+esc(s.kind)+'</small><p>'+esc(s.text)+'</p>'+(s.source_url?'<a target="_blank" rel="noopener" href="'+esc(s.source_url)+'">Read supporting source ↗</a>':'')+'</section>').join('');panel.querySelector('.brief-actions').before(narrative);const svg=infographic(b);panel.querySelector('.brief-preview').innerHTML=svg;
    panel.querySelector('[data-brief-md]').onclick=()=>download(markdown(b),'text/markdown;charset=utf-8','fynura-evidence-brief.md');
    panel.querySelector('[data-brief-svg]').onclick=()=>download(svg,'image/svg+xml','fynura-evidence-infographic.svg');
    panel.querySelector('[data-brief-png]').onclick=async()=>{
      const status=panel.querySelector('.brief-status'),url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));
      try{status.textContent='Preparing PNG…';const img=new Image();await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url});const canvas=document.createElement('canvas');canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;canvas.getContext('2d').drawImage(img,0,0);const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(!blob)throw Error('PNG unavailable');download(blob,'image/png','fynura-evidence-infographic.png');status.textContent='PNG prepared. Review the sources and limitations before sharing.'}catch{status.textContent='PNG could not be prepared. Download the SVG or report brief instead.'}finally{URL.revokeObjectURL(url)}
    };
  };
  const style=document.createElement('style');style.textContent='.generated-brief{border:1px solid #bcd4c5;border-radius:14px;padding:18px;margin-top:18px;background:#f2f8f3}.brief-actions{display:flex;flex-wrap:wrap;gap:8px}.brief-actions button,.brief-request button{border:1px solid #bfd4c5;border-radius:9px;background:#fff;padding:10px;color:#125e42;cursor:pointer}.brief-preview svg{width:100%;height:auto;display:block}.brief-preview{max-height:650px;overflow:auto;margin-top:14px}.brief-request{display:flex;flex-wrap:wrap;gap:10px;padding:12px 0}.brief-status{font-size:12px;line-height:1.5}';document.head.append(style);
  const actions=document.createElement('div');actions.className='brief-request';actions.innerHTML='<button>Create report brief</button><button>Create infographic</button>';
  document.querySelector('#ask .intro').append(actions);
  actions.children[0].onclick=()=>contextualAsk('Create a report brief about the selected evidence: where and who is affected, reported totals, trends, official response, sources and limitations.',intel.context);
  actions.children[1].onclick=()=>contextualAsk('Create an infographic about the selected evidence, including key figures, reporting dates and limitations.',intel.context);
})();
