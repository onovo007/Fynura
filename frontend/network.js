async function installEvidenceNetwork(){
  const response=await fetch('/api/sources'),registry=await response.json(),items=registry.sources;
  const orbit=document.querySelector('.orbit');
  orbit.outerHTML=`<aside class="network-hero"><small>GLOBAL EVIDENCE NETWORK</small><h2>Global evidence network</h2><strong>WHO · Africa CDC · ECDC · PAHO · CDC · National Health Authorities</strong><p>Authoritative evidence, reconciled where appropriate and traceable to source.</p><div class="network-flow"><div class="source-nodes">${items.map(s=>`<button data-source="${s.source_id}" class="${s.operational?'operational':s.integration_status}"><b>${s.display_name}</b><i>${s.operational?'Operational':s.integration_status.replace('_',' ')}</i></button>`).join('')}</div><div class="network-core"><span>F</span><b>FYNURA</b><small>VERIFIED INTELLIGENCE</small></div></div><em>Source definitions and reporting cutoffs remain visible.</em></aside>`;
  const sourceSection=document.createRange().createContextualFragment(`<section class="section source-explorer reveal visible" id="sources"><div class="heading"><div><p>05 / SOURCE EXPLORER</p><h2>Evidence has an identity.</h2></div><span>Every claim retains its source, reporting period, geography and verification history.</span></div><div class="source-grid">${items.map(s=>`<article><div><small>${s.scope.toUpperCase()} · ${s.region}</small><span class="source-status ${s.operational?'operational':s.integration_status}">${s.operational?'Operational':s.integration_status.replace('_',' ')}</span></div><h3>${s.display_name}</h3><p>${s.role}</p><dl><dt>Diseases</dt><dd>${s.diseases_supported.join(' · ')}</dd><dt>Resolution</dt><dd>${s.geographic_resolution.join(' · ')}</dd></dl><button data-source="${s.source_id}">Inspect source</button></article>`).join('')}</div></section>`);
  document.querySelector('#trust').before(sourceSection);
  document.querySelectorAll('[data-source]').forEach(button=>button.onclick=()=>showSource(items.find(source=>source.source_id===button.dataset.source)));
  const trustLabel=document.querySelector('#trust .heading p');
  if(trustLabel)trustLabel.textContent='06 / TRUST & METHODOLOGY';
}

function showSource(source){
  if(!source)return;
  const panel=document.querySelector('#health');panel.hidden=false;
  panel.innerHTML=`<div><strong>${source.organization}</strong><button aria-label="Close">×</button></div><dl><dt>Scope</dt><dd>${source.scope} · ${source.region}</dd><dt>Role</dt><dd>${source.role}</dd><dt>Fynura status</dt><dd>${source.operational?'Operational':source.integration_status.replace('_',' ')}</dd><dt>Evidence</dt><dd>${source.diseases_supported.join(' · ')}</dd><dt>Capabilities</dt><dd>${source.indicators_supported.join(' · ')}</dd></dl>`;
  panel.querySelector('button').onclick=()=>panel.hidden=true;
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>installEvidenceNetwork().catch(()=>{}));else installEvidenceNetwork().catch(()=>{});

async function installNigeriaAvailability(){
  const response=await fetch('/api/countries/nigeria/availability');
  if(!response.ok)return;
  const data=await response.json();
  const section=document.createRange().createContextualFragment(`<section class="section nigeria-availability reveal visible" id="nigeria-availability"><div class="heading"><div><p>NATIONAL SOURCE / NIGERIA</p><h2>Nigeria surveillance availability.</h2></div><span>Official NCDC aggregate reporting · ${data.status}</span></div><div class="availability-grid"><article><small>SOURCE STATUS</small><strong>${data.operational?'Operational':'Validation in progress'}</strong><p>${data.message}</p></article><article><small>GEOGRAPHIC COVERAGE</small><strong>National available after validation</strong><p>State and LGA views appear only when the source report explicitly publishes those rows and geography codes pass review.</p></article><article><small>REPORTING CUTOFF</small><strong>${data.last_epidemiological_cutoff||'No validated live observation'}</strong><p>Last refresh: ${data.last_refresh||'Not scheduled'}. A refresh time is never presented as an epidemiological reporting date.</p></article></div></section>`);
  const trust=document.querySelector('#trust');
  if(trust&&!document.querySelector('#nigeria-availability'))trust.before(section);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>installNigeriaAvailability().catch(()=>{}));else installNigeriaAvailability().catch(()=>{});
