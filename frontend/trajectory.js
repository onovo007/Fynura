/* Evidence-backed discrete charts; no interpolation between reporting dates. */
(() => {
  const original=showVisual;
  showVisual=function(id){
    intel.visualContext=null;
    original(id);
    const card=document.querySelector('#auto-visual'),a=intel.data[id],spec=intel.specs[id];
    if(!a||!spec)return;
    if(id==='ebola'){
      const names={confirmed_cases:'Confirmed cases',reported_deaths:'Deaths',crude_cfr:'Source-reported crude CFR',affected_health_zones:'Affected health zones'};
      const available=Object.keys(names).filter(k=>a.observations.filter(o=>o.indicator===k).length>1);
      card.querySelector('.chart-wrap').insertAdjacentHTML('beforebegin',`<label class="trajectory-selector">Trajectory metric <select aria-label="Ebola trajectory metric">${available.map(k=>`<option value="${k}">${names[k]}</option>`).join('')}</select></label>`);
      const select=card.querySelector('.trajectory-selector select');
      const countries=[...new Set(a.observations.filter(o=>o.indicator==='confirmed_cases').map(o=>o.geography.name))];
      select.parentElement.insertAdjacentHTML('beforebegin','<label class="trajectory-selector">Country / outbreak <select aria-label="Ebola country">'+countries.map(c=>'<option>'+safe(c)+'</option>').join('')+'</select></label><p class="trajectory-selector">Each line represents one country outbreak. Case and death totals are cumulative, not new cases per reporting period. Only countries with stored evidence are listed; historical outbreaks remain in Past events.</p>');
      const country=card.querySelector('[aria-label="Ebola country"]');
      const draw=()=>{
        const rows=a.observations.filter(o=>o.indicator===select.value&&o.geography.name===country.value).sort((a,b)=>a.reporting_period_end.localeCompare(b.reporting_period_end));
        if(!rows.length){card.querySelector('.chart-wrap').textContent='No compatible reports for this country and metric.';return}
        card.querySelector('.visual-toolbar h3').textContent='Ebola outbreak trajectory · '+country.value;
        intel.visualContext={...contextFor(id),geography:country.value,supporting_evidence_ids:rows.map(o=>o.observation_id),indicator:select.value};setContext(intel.visualContext);
        card.querySelector('.visual-toolbar p').textContent=names[select.value]+' across sequential compatible WHO reports';
        const max=Math.max(1,...rows.map(o=>o.value))*1.15, start=Date.parse(rows[0].reporting_period_end), duration=Date.parse(rows.at(-1).reporting_period_end)-start;
        const x=o=>85+(Date.parse(o.reporting_period_end)-start)/Math.max(1,duration)*720,y=o=>300-o.value/max*220;
        const grid=Array.from({length:5},(_,i)=>`<line x1="85" x2="805" y1="${300-i*55}" y2="${300-i*55}" style="stroke:#d8e2db;stroke-width:1"/><text x="70" y="${305-i*55}" text-anchor="end">${fmt(Math.round(max*i/4))}</text>`).join('');
        const line=rows.map(o=>`${x(o)},${y(o)}`).join(' ');
        const marks=rows.map(o=>`<circle cx="${x(o)}" cy="${y(o)}" r="6" fill="#177a58"><title>${safe(names[select.value])}: ${fmt(o.value)} ${safe(o.unit)}; reporting through ${displayDate(o.reporting_period_end)}; WHO; published ${displayDate(o.publication_date)}</title></circle><text x="${x(o)}" y="${y(o)-16}" text-anchor="middle">${fmt(o.value)}</text><text x="${x(o)}" y="330" text-anchor="middle">${displayDate(o.reporting_period_end)}</text>`).join('');
        card.querySelector('.chart-wrap').innerHTML=`<svg class="auto-chart" viewBox="0 0 900 370" role="img" aria-label="${safe(names[select.value])} across discrete WHO reporting dates">${grid}<polyline points="${line}" fill="none" stroke="#177a58" stroke-width="3"/>${marks}<text x="85" y="30">${safe(names[select.value])} · ${safe(rows[0].unit)}</text></svg><details><summary>Accessible data table</summary><table><thead><tr><th>Reporting through</th><th>${safe(names[select.value])}</th><th>Evidence</th></tr></thead><tbody>${rows.map(o=>`<tr><td>${displayDate(o.reporting_period_end)}</td><td>${fmt(o.value)}</td><td><a href="${safe(o.source_url)}" target="_blank" rel="noopener">WHO source</a></td></tr>`).join('')}</tbody></table></details>`;
      };
      select.onchange=draw;country.onchange=draw;draw();
    }
    if(id==='measles'||id==='cholera'){
      const disease=id==='measles'?'Measles':'Cholera';
      const rows=a.observations.filter(o=>o.indicator===(id==='measles'?'reported_measles_cases':'reported_cholera_awd_cases')&&o.geography.level==='country'&&o.reporting_period_end===spec.reporting_cutoff).sort((a,b)=>b.value-a.value);
      const controls=document.createElement('div');controls.className='epi-controls';
      controls.innerHTML='<label>Country view <select aria-label="'+disease+' country view"><option value="top">Top 10 countries</option><option value="all">All reporting countries</option>'+rows.map(o=>'<option value="'+safe(o.geography.name)+'">'+safe(o.geography.name)+'</option>').join('')+'</select></label>';
      const wrap=card.querySelector('.chart-wrap');wrap.before(controls);
      const draw=()=>{
        const choice=controls.querySelector('select').value,selected=choice==='top'?rows.slice(0,10):choice==='all'?rows:rows.filter(o=>o.geography.name===choice);
        const max=Math.max(1,...selected.map(o=>o.value)),height=Math.max(160,selected.length*38+45);
        card.querySelector('.visual-toolbar h3').textContent=disease+' reported cases by country';
        card.querySelector('.visual-toolbar p').textContent=id==='cholera'?'Cumulative reported cholera and acute watery diarrhoea cases in the stated reporting period':'Monthly reported measles cases';
        const geography=['top','all'].includes(choice)?'Global':choice;
        intel.visualContext={...contextFor(id),geography,supporting_evidence_ids:selected.map(o=>o.observation_id)};setContext(intel.visualContext);
        wrap.style.maxHeight='560px';wrap.style.overflow='auto';
        wrap.innerHTML='<p>'+selected.length+' of '+rows.length+' reporting countries shown · '+displayDate(spec.reporting_cutoff)+'. Not shown in the top ten does not mean zero cases. '+(id==='cholera'?'Cumulative reported cholera and acute watery diarrhoea cases.':'Monthly reported measles cases.')+'</p><svg viewBox="0 0 940 '+height+'" style="width:100%;min-width:650px" role="img" aria-label="Selected countries, '+disease+' reported cases">'+selected.map((o,i)=>'<g tabindex="0"><title>'+safe(o.geography.name)+': '+fmt(o.value)+' reported cases; '+displayDate(o.reporting_period_end)+'</title><text x="5" y="'+(30+i*38)+'" fill="#143b2c" font-size="13">'+safe(o.geography.name)+'</text><rect x="270" y="'+(14+i*38)+'" width="'+(o.value/max*560)+'" height="23" fill="#16845f"/><text x="'+(280+o.value/max*560)+'" y="'+(30+i*38)+'" fill="#143b2c" font-size="13">'+fmt(o.value)+'</text></g>').join('')+'</svg>';
        if(!rows.length)wrap.innerHTML='<p>No comparable country reports are available for this period. Missing reports are not zero.</p>';
        card.querySelector('.visual-footer p').textContent='Country-reported case volumes for the stated reporting period. Not population-adjusted risk.';
        if(id==='cholera')card.querySelectorAll('.visual-footer p')[1].textContent='Cholera and acute watery diarrhoea are reported together. Country counts are not added to overlapping global totals; absence of a country does not mean zero cases.';
      };controls.querySelector('select').onchange=draw;draw();
    }
    const actions=document.createElement('div');actions.className='epi-controls';
    actions.innerHTML='<button type="button">Download PNG</button><button type="button">Copy citation</button>';
    card.append(actions);
    actions.children[1].onclick=()=>navigator.clipboard.writeText(`${spec.source_label}. ${card.querySelector('.visual-toolbar h3').textContent}. ${intel.visualContext?.geography||spec.geography}. Reporting through ${spec.reporting_cutoff}. ${spec.source_url}. Accessed ${spec.retrieved_at}. Visualization: Fynura.`).then(()=>toast('Citation copied'));
    actions.children[0].onclick=async()=>{
      const spec={...intel.specs[id],title:card.querySelector('.visual-toolbar h3').textContent,geography:intel.visualContext?.geography||intel.specs[id].geography};
      const canvas=document.createElement('canvas');canvas.width=1400;canvas.height=850;const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,1400,850);ctx.fillStyle='#163d2c';ctx.font='bold 28px Arial';ctx.fillText('FYNURA · '+spec.title,40,55);ctx.font='18px Arial';ctx.fillText(`${id.toUpperCase()} · ${spec.geography} · Reporting through ${spec.reporting_cutoff}`,40,90);
      const svg=card.querySelector('svg');
      if(svg){const copy=svg.cloneNode(true);copy.setAttribute('xmlns','http://www.w3.org/2000/svg');copy.querySelectorAll('text').forEach(t=>{t.setAttribute('fill','#163d2c');t.setAttribute('font-family','Arial');t.setAttribute('font-size','15')});copy.querySelectorAll('rect,circle').forEach(t=>{if(!t.hasAttribute('fill'))t.setAttribute('fill','#177a58')});const blob=new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml'}),url=URL.createObjectURL(blob),img=new Image();try{await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url});ctx.drawImage(img,30,120,1340,550)}finally{URL.revokeObjectURL(url)}}else{ctx.font='24px Arial';spec.points.forEach((p,i)=>ctx.fillText(`${p.label}: ${fmt(p.value)} ${p.unit}`,40,160+i*50))}
      ctx.font='16px Arial';ctx.fillText('Data source: '+spec.source_label,40,730);ctx.fillText(String(spec.source_url),40,760);ctx.fillText('Visualization: Fynura · Generated '+new Date().toISOString(),40,795);
      const link=document.createElement('a');link.href=canvas.toDataURL('image/png');link.download=`fynura-${id}.png`;link.click();
    };
  };
  if(intel.specs[intel.active])showVisual(intel.active);
})();
