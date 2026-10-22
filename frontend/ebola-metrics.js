/* WHO Ebola table coverage: source blanks remain visibly distinct from zero. */
(() => {
  const columns = [
    ['suspected_cases','Suspected'], ['confirmed_cases','Confirmed'],
    ['reported_deaths','Confirmed deaths'], ['probable_cases','Probable'],
    ['probable_deaths','Probable deaths'], ['crude_cfr','Confirmed CFR'],
    ['recovered_cases','Recovered']
  ];
  const countries = ['COD','UGA','FRA','KEN','NGA'];
  const labels = {suspected_cases:'Suspected cases',probable_cases:'Probable cases',probable_deaths:'Probable deaths',recovered_cases:'Recovered'};
  const value = observation => observation ? `${fmt(observation.value)}${observation.unit==='percent'?'%':''}` : '<span>Not reported</span>';
  function latest(rows, indicator, iso3){
    return rows.filter(o=>o.source_id==='who_ebola_alert'&&o.indicator===indicator&&o.geography.iso3===iso3)
      .sort((a,b)=>String(b.reporting_period_end).localeCompare(String(a.reporting_period_end)))[0];
  }
  function installOptions(){
    const select=document.querySelector('#map-metric');if(!select)return false;
    [['suspected_cases','Suspected cases'],['probable_cases','Probable cases'],['probable_deaths','Probable deaths'],['recovered_cases','Recovered']].forEach(([id,label])=>{
      if(!select.querySelector(`[value="${id}"]`))select.add(new Option(label,id),select.querySelector('[value="rate_per_100k"]'));
    });
    const reported=select.querySelector('[value="reported_cases"]');if(reported)reported.textContent='Confirmed/reported cases';
    const deaths=select.querySelector('[value="deaths"]');if(deaths)deaths.textContent='Confirmed/reported deaths';
    const cfr=select.querySelector('[value="cfr"]');if(cfr)cfr.textContent='Confirmed CFR';
    return true;
  }
  function render(){
    if(!installOptions()||!intel?.data?.ebola)return;
    const coverage=document.querySelector('#map-coverage');if(!coverage)return;
    document.querySelector('#ebola-metric-matrix')?.remove();
    if(document.querySelector('#map-disease').value!=='ebola')return;
    const rows=intel.data.ebola.observations;
    const names={};rows.forEach(o=>{if(o.geography.iso3)names[o.geography.iso3]=o.geography.name});
    const selected=document.querySelector('#map-metric').value;
    const indicator={signal:'confirmed_cases',reported_cases:'confirmed_cases',deaths:'reported_deaths',cfr:'crude_cfr'}[selected]||selected;
    const available=countries.filter(code=>latest(rows,indicator,code));
    const missing=countries.filter(code=>!latest(rows,indicator,code)).map(code=>names[code]||code);
    const section=document.createElement('details');section.id='ebola-metric-matrix';section.className='map-metric-matrix';section.innerHTML=`
      <summary>WHO Ebola country metric table <b>${available.length} of ${countries.length} countries report ${safe(labels[indicator]||columns.find(c=>c[0]===indicator)?.[1]||'this metric')}</b></summary>
      ${missing.length?`<p>The WHO table does not report this metric for ${safe(missing.join(' and '))}. Their confirmed-case rows remain available; missing values are not zero.</p>`:'<p>This metric is reported for every affected country in the current WHO table.</p>'}
      <div class="metric-matrix-scroll"><table><thead><tr><th>Country</th>${columns.map(c=>`<th>${c[1]}</th>`).join('')}<th>Cutoff</th></tr></thead><tbody>${countries.map(code=>{
        const anchor=latest(rows,'confirmed_cases',code)||columns.map(c=>latest(rows,c[0],code)).find(Boolean);
        return `<tr><th>${safe(names[code]||code)}</th>${columns.map(c=>`<td>${value(latest(rows,c[0],code))}</td>`).join('')}<td>${anchor?displayDate(anchor.reporting_period_end):'Not stated'}</td></tr>`;
      }).join('')}</tbody></table></div>
      <small>Values reproduce the WHO affected-country table. Country reporting cutoffs differ, so rows are not recomputed into a new total. <a href="${safe(rows.find(o=>o.source_id==='who_ebola_alert')?.source_url||'#')}" target="_blank" rel="noopener">Open WHO source →</a></small>`;
    coverage.after(section);
  }
  const observer=new MutationObserver(()=>queueMicrotask(render));
  function start(){if(installOptions()){const coverage=document.querySelector('#map-coverage');if(coverage)observer.observe(coverage,{childList:true,subtree:true});document.querySelectorAll('#map-disease,#map-region,#map-metric').forEach(x=>x.addEventListener('change',()=>setTimeout(render,80)));render()}else setTimeout(start,100)}
  window.addEventListener('fynura:intelligence',render);document.readyState==='loading'?addEventListener('DOMContentLoaded',start):start();
})();
