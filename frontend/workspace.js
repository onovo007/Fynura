/* Shared, source-backed analytical context. Never sum overlapping observations. */
(() => {
  const filters={threat:'all',region:'Global',country:'',period:''};
  let sequence=0,current=null;
  const css=document.createElement('link');css.rel='stylesheet';css.href='/static/workspace.css?v=1';document.head.append(css);
  const preserve=document.createElement('link');preserve.rel='stylesheet';preserve.href='/static/workspace-preserve.css?v=1';document.head.append(preserve);
  const fetchBefore=window.fetch.bind(window);
  window.fetch=(input,options)=>{
    if(typeof input==='string'&&input.startsWith('/api/map?')){
      const url=new URL(input,location.origin);url.searchParams.set('country',filters.country);url.searchParams.set('period',filters.period);input=url.pathname+url.search;
    }
    return fetchBefore(input,options);
  };
  const esc=value=>safe(String(value??'Not stated'));
  const label=value=>value==='reported_cholera_awd_cases'?'Reported cholera and acute watery diarrhoea cases':String(value).replaceAll('_',' ');
  const dates=m=>'<dl class="period-strip"><div><dt>Reporting period</dt><dd>'+esc(m.reporting_start?displayDate(m.reporting_start)+' – '+displayDate(m.reporting_cutoff):(m.threat==='measles'&&m.reporting_cutoff?new Date(m.reporting_cutoff+'T00:00:00').toLocaleDateString('en-GB',{month:'long',year:'numeric'}):'Through '+displayDate(m.reporting_cutoff)))+'</dd></div><div><dt>Reporting cutoff</dt><dd>'+esc(displayDate(m.reporting_cutoff))+'</dd></div><div><dt>Published</dt><dd>'+esc(displayDate(m.publication_date))+'</dd></div><div><dt>Retrieved</dt><dd>'+esc(m.retrieved_at?new Date(m.retrieved_at).toLocaleString():'Not stated')+'</dd></div></dl>';
  function controls(){
    if(document.querySelector('#workspace-filters'))return;
    const cards=document.querySelector('.cards');if(!cards)return;
    const box=document.createElement('div');box.id='workspace-filters';box.className='shared-filters';
    box.innerHTML='<p>Shared analytical scope · cards, map, table, visuals and Ask Fynura</p><label>Threat<select name="threat"><option value="all">All threats</option><option value="measles">Measles</option><option value="ebola">Ebola</option><option value="cholera">Cholera</option></select></label><label>WHO region<select name="region"><option>Global</option></select></label><label>Country<select name="country"><option value="">All available countries</option></select></label><label>Reporting period<select name="period"><option value="">Latest verified</option></select></label><button type="button" id="workspace-reset">Reset filters</button><p role="status" id="workspace-status"></p>';
    cards.before(box);
    box.addEventListener('change',e=>{filters[e.target.name]=e.target.value;if(['threat','region'].includes(e.target.name)){filters.country='';filters.period=''}apply();productEvent('map_filter_used','shared_filters',filters.threat==='all'?undefined:filters.threat)});
    box.querySelector('button').onclick=()=>{Object.assign(filters,{threat:'all',region:'Global',country:'',period:''});apply()};
    document.addEventListener('change',e=>{if(e.target.id==='map-disease'||e.target.id==='map-region'){filters[e.target.id==='map-disease'?'threat':'region']=e.target.value;filters.country='';filters.period='';apply()}});
  }
  function options(name,rows,empty){
    const select=document.querySelector('#workspace-filters [name="'+name+'"]');select.replaceChildren(new Option(empty,name==='region'?'Global':''));
    rows.forEach(row=>select.add(new Option(row.name||row,row.code||row)));select.value=filters[name];
    if(select.selectedIndex<0){filters[name]=name==='region'?'Global':'';select.value=filters[name]}
  }
  function context(id){
    const country=current?.schema.countries.find(c=>c.code===filters.country);
    return {threat_id:id,disease:id,geography:country?.name||(filters.region!=='Global'?filters.region:'Global'),region:filters.region,
      reporting_cutoff:filters.period||null,visual:'shared_workspace',visual_context:{country:filters.country,period:filters.period},
      supporting_evidence_ids:current?.metrics.filter(m=>!id||m.threat===id).flatMap(m=>m.evidence_ids)||[]};
  }
  function inspect(index){
    const m=current.metrics[index];document.querySelector('#evidence').innerHTML='<article class="evidence-item"><h2>'+esc(m.threat.toUpperCase()+' · '+m.geography.name)+'</h2><h3>'+esc(label(m.indicator))+'</h3><strong>'+ (m.value==null?'Unresolved conflict':fmt(m.value))+'</strong>'+dates(m)+'<p>Primary source: '+esc(m.primary_source||'None selected')+'</p><p>Evidence confidence: '+Math.round(m.confidence*100)+'% · operational evidence score, not disease probability.</p><p>Selection rationale: '+esc(m.selection_rationale.join(' · '))+'</p><p>Source agreement: '+(m.source_agreement?'Yes':'No')+'</p><p>Conflicts: '+esc(m.conflicts.join('; ')||'None reported')+'</p><p>Independent corroborating observations: '+m.corroborating.length+'</p><p>Age/sex disaggregation: not available in this dataset.</p>'+m.evidence.map(o=>'<section><h3>'+esc(o.source_id)+'</h3><p>'+fmt(o.value)+' '+esc(o.unit)+' · '+esc(o.case_definition)+'</p><a target="_blank" rel="noopener" href="'+esc(o.source_url)+'">Inspect original evidence →</a>'+dates({reporting_start:o.reporting_period_start,reporting_cutoff:o.reporting_period_end,publication_date:o.publication_date,retrieved_at:o.retrieved_at})+'</section>').join('')+'</article>';
    document.querySelector('#drawer').showModal();productEvent('evidence_opened','canonical_evidence',m.threat);
  }
  function render(){
    const groups=new Map();current.metrics.forEach((m,i)=>{const key=m.threat+'|'+m.geography.name;if(!groups.has(key))groups.set(key,[]);groups.get(key).push({...m,index:i})});
    const cards=document.querySelector('.cards');cards.innerHTML=groups.size?Array.from(groups.values()).map(rows=>{
      const primary=rows.find(m=>['confirmed_cases','reported_measles_cases_global','reported_measles_cases','reported_cholera_awd_cases'].includes(m.indicator))||rows[0];
      return '<article class="canonical-card"><small>'+esc(primary.threat.toUpperCase())+' · '+esc(primary.geography.name)+'</small><h3>'+esc(label(primary.indicator))+'</h3><strong class="canonical-value">'+(primary.value==null?'Unresolved':fmt(primary.value))+'</strong><span>'+esc(primary.unit)+'</span>'+dates(primary)+'<p>Primary source: '+esc(primary.primary_source||'Not selected')+'</p><p>Evidence confidence: '+Math.round(primary.confidence*100)+'%</p><button data-canonical="'+primary.index+'">Inspect evidence and confidence</button><details><summary>All verified metrics ('+rows.length+')</summary>'+rows.map(m=>'<p>'+esc(label(m.indicator))+': '+(m.value==null?'Unresolved':fmt(m.value))+' '+esc(m.unit)+' <button data-canonical="'+m.index+'">Evidence</button></p>').join('')+'</details></article>';
    }).join(''):'<p class="canonical-empty">'+esc(current.empty_message)+'</p>';
    let table=document.querySelector('#canonical-table');if(!table){table=document.createElement('section');table.id='canonical-table';table.className='epi-panel';document.querySelector('#visuals').before(table)}
    table.innerHTML='<h2>Epidemiological intelligence</h2><p>Source-selected observations. No inferred demographic distributions or summed overlapping reports.</p><div class="epi-scroll"><table><thead><tr><th>Threat</th><th>Geography</th><th>Indicator</th><th>Value</th><th>Reporting cutoff</th><th>Evidence</th></tr></thead><tbody>'+current.metrics.map((m,i)=>'<tr><td>'+esc(m.threat)+'</td><td>'+esc(m.geography.name)+'</td><td>'+esc(label(m.indicator))+'</td><td>'+(m.value==null?'Unresolved':fmt(m.value))+' '+esc(m.unit)+'</td><td>'+esc(displayDate(m.reporting_cutoff))+'</td><td><button data-canonical="'+i+'">Inspect</button></td></tr>').join('')+'</tbody></table></div>';
    document.body.classList.add('workspace-active');
    const download=document.createElement('button');download.type='button';download.textContent='Download selected evidence CSV';
    download.onclick=()=>{
      const fields=['threat','indicator','value','unit','reporting_start','reporting_cutoff','publication_date','retrieved_at','primary_source','source_url','confidence'];
      const lines=[fields,...current.metrics.map(m=>fields.map(k=>m[k]??''))];
      const csv=lines.map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n');
      const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'})),link=document.createElement('a');link.href=url;link.download='fynura-selected-evidence.csv';link.click();URL.revokeObjectURL(url);
    };table.prepend(download);
    document.querySelectorAll('[data-canonical]').forEach(b=>b.onclick=()=>inspect(Number(b.dataset.canonical)));
    setContext(context(filters.threat==='all'?null:filters.threat));
  }
  const originalContext=contextFor;
  contextFor=function(id,spec){return current&&(filters.country||filters.region!=='Global'||filters.period)?context(id):originalContext(id,spec)};
  const originalVisual=showVisual;
  showVisual=function(id){
    originalVisual(id);
    const card=document.querySelector('#auto-visual'),spec=intel.specs[id],a=intel.data[id];if(!spec||!a)return;
    const rows=a.observations.filter(o=>spec.supporting_evidence_ids.includes(o.observation_id));
    const o=rows.find(o=>o.reporting_period_end===spec.reporting_cutoff)||rows[0];
    if(o)card.querySelector('.visual-toolbar').insertAdjacentHTML('afterend',dates({reporting_start:o.reporting_period_start,reporting_cutoff:spec.reporting_cutoff,publication_date:o.publication_date,retrieved_at:spec.retrieved_at}));
    if(id!=='ebola')card.querySelector('.visual-toolbar h3')?.insertAdjacentText('beforeend',' · surveillance snapshot');
    if(filters.country||filters.region!=='Global'||filters.period){
      const metrics=current?.metrics.filter(m=>m.threat===id)||[];
      card.innerHTML='<div class="visual-toolbar"><h3>'+esc(id.toUpperCase())+' · selected-scope snapshot</h3><p>Selected region/country/reporting period. Source-reported values, not a regional sum.</p></div>'+ (metrics.length?metrics.map(m=>'<article class="scoped-metric"><h4>'+esc(m.geography.name+' · '+label(m.indicator))+'</h4><strong>'+(m.value==null?'Unresolved':fmt(m.value))+' '+esc(m.unit)+'</strong>'+dates(m)+'</article>').join(''):'<p>'+esc(current?.empty_message)+'</p>');
      const history=(current?.history||[]).filter(o=>o.threat_id===id&&['confirmed_cases','reported_measles_cases','reported_cholera_awd_cases','reported_measles_cases_global'].includes(o.indicator));
      const compatible=new Set(history.map(o=>[o.geography.name,o.indicator,o.unit,o.case_definition].join('|'))).size===1;
      if(compatible&&new Set(history.map(o=>o.reporting_period_end)).size>1){
        history.sort((a,b)=>a.reporting_period_end.localeCompare(b.reporting_period_end));
        const toggle=document.createElement('button');toggle.textContent='Trend over time';toggle.type='button';card.prepend(toggle);
        toggle.onclick=()=>{
          const max=Math.max(1,...history.map(o=>o.value)),start=Date.parse(history[0].reporting_period_end),span=Date.parse(history.at(-1).reporting_period_end)-start;
          const x=o=>70+700*(Date.parse(o.reporting_period_end)-start)/span,y=o=>260-210*o.value/max;
          let plot=card.querySelector('.scope-trend');if(plot){plot.remove();toggle.textContent='Trend over time';return}
          plot=document.createElement('div');plot.className='scope-trend';plot.innerHTML='<h3>Compatible reporting-period trend</h3><svg viewBox="0 0 850 340" role="img" aria-label="Source-backed observations over reporting dates"><polyline fill="none" stroke="#16815d" stroke-width="3" points="'+history.map(o=>x(o)+','+y(o)).join(' ')+'"/>'+history.map(o=>'<circle r="5" fill="#16815d" cx="'+x(o)+'" cy="'+y(o)+'"/><text text-anchor="middle" x="'+x(o)+'" y="'+(y(o)-12)+'">'+fmt(o.value)+'</text><text text-anchor="middle" x="'+x(o)+'" y="300">'+esc(displayDate(o.reporting_period_end))+'</text>').join('')+'</svg><p>Compatible '+esc(history[0].case_definition)+' observations in '+esc(history[0].unit)+'. Reporting changes are not necessarily incident cases.</p>';
          toggle.after(plot);toggle.textContent='Hide trend';
        };
      }
    }
    setContext(context(filters.threat==='all'?null:id));productEvent('chart_viewed','visualization',id);
  };
  async function apply(){
    controls();if(!document.querySelector('#workspace-filters'))return;
    const serial=++sequence;document.querySelector('#workspace-status').textContent='Loading verified scope…';
    try{
      const response=await fetch('/api/workspace?'+new URLSearchParams(filters));if(!response.ok)throw Error('Evidence scope could not be loaded.');
      const data=await response.json();if(serial!==sequence)return;current=data;
      options('region',data.schema.regions,'Global');options('country',data.schema.countries,'All available countries');options('period',data.schema.periods,'Latest verified');
      document.querySelector('#workspace-filters [name=threat]').value=filters.threat;
      for(const [id,key] of [['map-disease','threat'],['map-region','region']])if(document.getElementById(id))document.getElementById(id).value=filters[key];
      render();renderMap();showVisual(filters.threat==='all'?(data.metrics.some(m=>m.threat===intel.active)?intel.active:(data.metrics[0]?.threat||intel.active)):filters.threat);
      document.querySelector('#workspace-status').textContent=data.metrics.length?data.metrics.length+' verified metric selections':data.empty_message;
    }catch(error){document.querySelector('#workspace-status').textContent=error.message}
  }
  window.addEventListener('fynura:intelligence',apply);
  document.addEventListener('click',e=>{const target=e.target.closest('button,a,summary');if(!target)return;
    if(target.dataset.threat){filters.threat=target.dataset.threat;filters.country='';filters.period='';apply()}
    const event=target.matches('[data-source]')?'source_opened':target.closest('.early-grid')?'early_signal_viewed':target.closest('.story-controls')?null:/citation/i.test(target.textContent)?'citation_copied':/download/i.test(target.textContent)?'visual_downloaded':target.matches('[aria-label="Start voice question"]')?'voice_used':null;
    if(event)productEvent(event,'workspace',filters.threat==='all'?undefined:filters.threat);
  });
  const askBefore=contextualAsk;
  contextualAsk=async function(question,provided){if((question||document.querySelector('#chat-q')?.value||'').trim())productEvent('ask_fynura_submitted','ask_fynura',filters.threat==='all'?undefined:filters.threat);return askBefore(question,provided)};
  if(Object.keys(intel.data).length)apply();
})();
