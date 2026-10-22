/* Transparent surveillance review priorities; recommendations are opened in Ask Fynura. */
(() => {
  function create(){
    if(document.querySelector('#priority-advisor'))return;
    const section=document.createElement('section');section.id='priority-advisor';section.className='section priority-advisor reveal visible';section.innerHTML=`
      <div class="heading"><div><p>SURVEILLANCE REVIEW PRIORITIES</p><h2>Turn verified evidence into focused review.</h2></div><span>Compare reporting recency, confirmed activity and data gaps before opening a source-grounded advisory.</span></div>
      <div class="priority-controls"><label>Threat<select id="priority-threat"><option value="ebola">Ebola</option><option value="measles">Measles</option><option value="cholera">Cholera</option></select></label><button id="priority-update">Update review</button></div>
      <p id="priority-status" role="status">Loading verified observations…</p><div id="priority-results" class="priority-results"></div>
      <div class="priority-action"><div><b>Need an interpretation?</b><p>Ask Fynura to connect these observations with current official guidance, while separating evidence from suggested actions.</p></div><button id="priority-ask">Ask Fynura for an advisory</button></div>`;
    document.querySelector('#event-intelligence, #trust')?.before(section);
    document.querySelector('[data-workspace-link="learn"]')?.replaceChildren('Prioritize');
    section.querySelector('#priority-update').onclick=render;
    section.querySelector('#priority-threat').onchange=render;
    section.querySelector('#priority-ask').onclick=()=>{
      const threat=section.querySelector('#priority-threat').value;
      contextualAsk(`Using the verified ${threat} observations in Fynura and current official guidance, identify where surveillance review, case finding, data verification, risk communication, or control planning may need attention. Separate observed evidence from suggested actions, cite sources, and do not infer population risk from raw totals alone.`,contextFor(threat));
      document.querySelector('[data-workspace-link="advise"]')?.click();
    };
  }
  function render(){
    create();if(!intel?.data||!Object.keys(intel.data).length)return;
    const threat=document.querySelector('#priority-threat').value,a=intel.data[threat];
    const observations=a?.observations||[], indicator=threat==='measles'?'reported_measles_cases':threat==='cholera'?'reported_cholera_awd_cases':'confirmed_cases';
    const latest={};observations.filter(o=>o.indicator===indicator&&o.geography.level==='country').forEach(o=>{const key=o.geography.iso3||o.geography.name,c=latest[key];if(!c||String(o.reporting_period_end)>String(c.reporting_period_end))latest[key]=o});
    let rows=Object.values(latest).sort((a,b)=>String(b.reporting_period_end).localeCompare(String(a.reporting_period_end))).slice(0,8);
    if(!rows.length){const global=observations.filter(o=>o.indicator===indicator).sort((a,b)=>String(b.reporting_period_end).localeCompare(String(a.reporting_period_end)))[0];if(global)rows=[global]}
    document.querySelector('#priority-status').textContent=`${rows.length} current reporting ${rows.length===1?'scope':'scopes'} available for review. This is a review aid, not an automated alert or resource-allocation decision.`;
    document.querySelector('#priority-results').innerHTML=rows.map(o=>{
      const country=o.geography.name,iso=o.geography.iso3,metrics=observations.filter(x=>(x.geography.iso3||x.geography.name)===(iso||country)&&String(x.reporting_period_end)===String(o.reporting_period_end));
      const missing=threat==='ebola'?[['reported_deaths','deaths'],['crude_cfr','CFR'],['recovered_cases','recoveries']].filter(([id])=>!metrics.some(x=>x.indicator===id)).map(x=>x[1]):[];
      return `<article><small>${safe(threat.toUpperCase())}</small><h3>${safe(country)}</h3><strong>${fmt(o.value)} <span>${safe(o.unit)}</span></strong><p>Reporting through ${displayDate(o.reporting_period_end)}</p>${missing.length?`<em>Review data completeness: ${safe(missing.join(', '))} not reported in this row.</em>`:'<em>Core table metrics available for this reporting row.</em>'}<a href="${safe(o.source_url)}" target="_blank" rel="noopener">Inspect source →</a></article>`;
    }).join('')||'<p>No compatible country observations are stored for this selection.</p>';
  }
  window.addEventListener('fynura:intelligence',render);document.readyState==='loading'?addEventListener('DOMContentLoaded',create):create();setTimeout(render,1000);
})();
