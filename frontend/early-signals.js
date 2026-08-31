(() => {
  let chosen='USA', requestId=0;
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function plot(points,key,title) {
    const max=Math.max(1,...points.map(p=>p[key]),...(key==='value'?points.map(p=>p.expected):[5]));
    const x=i=>60+i*660/Math.max(1,points.length-1),y=v=>190-v/max*150;
    const line=k=>points.map((p,i)=>`${x(i)},${y(p[k])}`).join(' ');
    return `<svg viewBox="0 0 780 245" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title><text x="60" y="18">${esc(title)}</text>${[0,.5,1].map(f=>`<line x1="60" x2="725" y1="${y(max*f)}" y2="${y(max*f)}" stroke="#dce6df"/><text x="4" y="${y(max*f)+4}" font-size="11">${Math.round(max*f).toLocaleString()}</text>`).join('')}${key==='value'?`<polyline fill="none" stroke="#8a9bab" stroke-dasharray="5 4" points="${line('expected')}"/>`:`<line x1="60" x2="725" y1="${y(5)}" y2="${y(5)}" stroke="#b76928" stroke-dasharray="5 4"/>`}<polyline fill="none" stroke="#13845c" stroke-width="3" points="${line(key)}"/>${points.map((p,i)=>`<circle tabindex="0" cx="${x(i)}" cy="${y(p[key])}" r="4" fill="#13845c"><title>${esc(p.period)}: ${p[key].toLocaleString()}${key==='value'?` reported cases; monthly baseline ${p.expected}`:' CUSUM; threshold 5'}</title></circle>`).join('')}<text x="60" y="220" font-size="12">${esc(points[0].period)}</text><text x="720" y="220" text-anchor="end" font-size="12">${esc(points.at(-1).period)}</text></svg>`;
  }
  async function load(panel) {
    const id=++requestId;
    panel.innerHTML='<h3>Changes in reported cases</h3><p role="status">Loading historical comparisons…</p>';
    try{
      const response=await fetch('/api/early-signals?country='+encodeURIComponent(chosen));if(!response.ok)throw Error('Historical comparisons are temporarily unavailable.');
      const d=await response.json();if(id!==requestId)return;
      panel.innerHTML=`<small>EARLY SIGNALS · HISTORICAL REVIEW</small><h3>Changes in reported cases</h3><p>Explore whether recent monthly reports differ from the country’s historical pattern.</p><label>Measles · Country <select aria-label="Signal review country">${d.countries.map(c=>`<option value="${esc(c.code)}" ${c.code===d.country?'selected':''}>${esc(c.name)}</option>`).join('')}</select></label><article class="signal-main"><strong>${esc(d.status)}</strong><p>${esc(d.geography)}${d.reporting_cutoff?' · Reports through '+esc(d.reporting_cutoff):''}</p>${d.ready?`<div class="signal-plots">${plot(d.points,'value','Reported cases and monthly baseline')}${plot(d.points,'cusum','CUSUM comparison')}</div><p>Green: reported cases or CUSUM. Dashed lines: monthly baseline or comparison threshold.</p><details><summary>Data and calculation</summary><p>Baseline: ${esc(d.baseline_start)} to ${esc(d.baseline_end)}. ${esc(d.method)}</p><table><thead><tr><th>Month</th><th>Cases</th><th>Baseline</th><th>CUSUM</th></tr></thead><tbody>${d.points.map(p=>`<tr><td>${esc(p.period)}</td><td>${p.value}</td><td>${p.expected}</td><td>${p.cusum}</td></tr>`).join('')}</tbody></table></details>`:''}<p>${esc(d.note)}</p><a href="${esc(d.source_url)}" target="_blank" rel="noopener">WHO monthly reports ↗</a> · <a href="/docs#early-signals">How this comparison works</a></article><div class="signal-coverage">${d.coverage.map(c=>`<article><small>${esc(c.threat)}</small><strong>${esc(c.status)}</strong><p>${esc(c.description)}</p></article>`).join('')}</div>`;
      panel.querySelector('select').onchange=e=>{chosen=e.target.value;load(panel)};
      const ifr=document.createElement('p');ifr.textContent='IFR: Not estimable from current surveillance data.';ifr.title='Infection fatality ratio requires total infections, including infections not reported as cases.';panel.append(ifr);
      const askButton=document.createElement('button');askButton.type='button';askButton.textContent='Ask about this signal';
      askButton.onclick=()=>{document.querySelector('#ask').scrollIntoView({behavior:'smooth'});window.researchAsk('Explain this early signal and its baseline, threshold and limitations.',{visual:'early_signal',threat_id:'measles',geography:d.geography,visual_context:{country:d.country}});};
      panel.querySelector('.signal-main').append(askButton);
    }catch(error){panel.innerHTML=`<h3>Changes in reported cases</h3><p>${esc(error.message)}</p><button type="button">Retry</button>`;panel.querySelector('button').onclick=()=>load(panel);}
  }
  function mount(){const old=document.querySelector('#epi-intelligence .early-grid');if(!old)return;
    old.previousElementSibling?.remove();old.previousElementSibling?.remove();
    const panel=document.createElement('section');panel.className='signal-review';old.replaceWith(panel);load(panel);
  }
  new MutationObserver(mount).observe(document.body,{childList:true,subtree:true});mount();
})();
