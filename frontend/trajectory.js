/* Evidence-backed discrete charts; no interpolation between reporting dates. */
(() => {
  const original=showVisual;
  showVisual=function(id){
    original(id);
    const card=document.querySelector('#auto-visual'),a=intel.data[id],spec=intel.specs[id];
    if(!a||!spec)return;
    if(id==='ebola'){
      const names={confirmed_cases:'Confirmed cases',reported_deaths:'Deaths',crude_cfr:'Source-reported crude CFR',affected_health_zones:'Affected health zones'};
      const available=Object.keys(names).filter(k=>a.observations.filter(o=>o.indicator===k).length>1);
      card.querySelector('.chart-wrap').insertAdjacentHTML('beforebegin',`<label class="trajectory-selector">Trajectory metric <select aria-label="Ebola trajectory metric">${available.map(k=>`<option value="${k}">${names[k]}</option>`).join('')}</select></label>`);
      const select=card.querySelector('.trajectory-selector select');
      const draw=()=>{
        const rows=a.observations.filter(o=>o.indicator===select.value).sort((a,b)=>a.reporting_period_end.localeCompare(b.reporting_period_end));
        card.querySelector('.visual-toolbar p').textContent=names[select.value]+' across sequential compatible WHO reports';
        const max=Math.max(1,...rows.map(o=>o.value))*1.15, start=Date.parse(rows[0].reporting_period_end), duration=Date.parse(rows.at(-1).reporting_period_end)-start;
        const x=o=>85+(Date.parse(o.reporting_period_end)-start)/Math.max(1,duration)*720,y=o=>300-o.value/max*220;
        const grid=Array.from({length:5},(_,i)=>`<line x1="85" x2="805" y1="${300-i*55}" y2="${300-i*55}" style="stroke:#d8e2db;stroke-width:1"/><text x="70" y="${305-i*55}" text-anchor="end">${fmt(Math.round(max*i/4))}</text>`).join('');
        const line=rows.map(o=>`${x(o)},${y(o)}`).join(' ');
        const marks=rows.map(o=>`<circle cx="${x(o)}" cy="${y(o)}" r="6" fill="#177a58"><title>${safe(names[select.value])}: ${fmt(o.value)} ${safe(o.unit)}; reporting through ${displayDate(o.reporting_period_end)}; WHO; published ${displayDate(o.publication_date)}</title></circle><text x="${x(o)}" y="${y(o)-16}" text-anchor="middle">${fmt(o.value)}</text><text x="${x(o)}" y="330" text-anchor="middle">${displayDate(o.reporting_period_end)}</text>`).join('');
        card.querySelector('.chart-wrap').innerHTML=`<svg class="auto-chart" viewBox="0 0 900 370" role="img" aria-label="${safe(names[select.value])} across discrete WHO reporting dates">${grid}<polyline points="${line}" fill="none" stroke="#177a58" stroke-width="3"/>${marks}<text x="85" y="30">${safe(names[select.value])} · ${safe(rows[0].unit)}</text></svg><details><summary>Accessible data table</summary><table><thead><tr><th>Reporting through</th><th>${safe(names[select.value])}</th><th>Evidence</th></tr></thead><tbody>${rows.map(o=>`<tr><td>${displayDate(o.reporting_period_end)}</td><td>${fmt(o.value)}</td><td><a href="${safe(o.source_url)}" target="_blank" rel="noopener">WHO source</a></td></tr>`).join('')}</tbody></table></details>`;
      };
      select.onchange=draw;draw();
    }
    const actions=document.createElement('div');actions.className='epi-controls';
    actions.innerHTML='<button type="button">Download PNG</button><button type="button">Copy citation</button>';
    card.append(actions);
    actions.children[1].onclick=()=>navigator.clipboard.writeText(`${spec.source_label}. ${spec.title}. Reporting through ${spec.reporting_cutoff}. ${spec.source_url}. Accessed ${spec.retrieved_at}. Visualization: Fynura.`).then(()=>toast('Citation copied'));
    actions.children[0].onclick=async()=>{
      const canvas=document.createElement('canvas');canvas.width=1400;canvas.height=850;const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,1400,850);ctx.fillStyle='#163d2c';ctx.font='bold 28px Arial';ctx.fillText('FYNURA · '+spec.title,40,55);ctx.font='18px Arial';ctx.fillText(`${id.toUpperCase()} · ${spec.geography} · Reporting through ${spec.reporting_cutoff}`,40,90);
      const svg=card.querySelector('svg');
      if(svg){const copy=svg.cloneNode(true);copy.setAttribute('xmlns','http://www.w3.org/2000/svg');copy.querySelectorAll('text').forEach(t=>{t.setAttribute('fill','#163d2c');t.setAttribute('font-family','Arial');t.setAttribute('font-size','15')});copy.querySelectorAll('rect,circle').forEach(t=>{if(!t.hasAttribute('fill'))t.setAttribute('fill','#177a58')});const blob=new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml'}),url=URL.createObjectURL(blob),img=new Image();try{await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url});ctx.drawImage(img,30,120,1340,550)}finally{URL.revokeObjectURL(url)}}else{ctx.font='24px Arial';spec.points.forEach((p,i)=>ctx.fillText(`${p.label}: ${fmt(p.value)} ${p.unit}`,40,160+i*50))}
      ctx.font='16px Arial';ctx.fillText('Data source: '+spec.source_label,40,730);ctx.fillText(String(spec.source_url),40,760);ctx.fillText('Visualization: Fynura · Generated '+new Date().toISOString(),40,795);
      const link=document.createElement('a');link.href=canvas.toDataURL('image/png');link.download=`fynura-${id}.png`;link.click();
    };
  };
  if(intel.specs[intel.active])showVisual(intel.active);
})();
