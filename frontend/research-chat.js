(() => {
  if(typeof installCopilot==='function')installCopilot();
  let busy = false;
  const history = [];
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function answerMarkup(data) {
    let text = data.answer;
    const insertions = new Map();
    for (const support of data.supports || []) {
      const start = text.indexOf(support.text);
      if (start < 0) continue;
      const end = start + support.text.length;
      insertions.set(end, [...new Set([...(insertions.get(end) || []), ...support.sources])]);
    }
    for (const [end, ids] of [...insertions.entries()].sort((a,b) => b[0]-a[0])) {
      text = text.slice(0,end) + ids.map(id => ` ⟦source:${id}⟧`).join('') + text.slice(end);
    }
    let html = escape(text.replaceAll(String.fromCharCode(8212), ', ')).replace(/\[([^\]]+)\]\(https?:\/\/[^)]+\)/g, '$1');
    html = html.replace(/⟦source:(\d+)⟧/g, (_,id) => {
      const source = data.sources.find(s => s.id === Number(id));
      return source ? `<a class="research-cite" href="${escape(source.url)}" target="_blank" rel="noopener noreferrer" aria-label="Source ${id}: ${escape(source.title)}">[${id}]</a>` : '';
    });
    return html.replace(/^#{1,4} (.+)$/gm, '<h4>$1</h4>').replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>').replace(/^[-*] /gm,'• ');
  }
  function render(data) {
    const section = document.createElement('section');
    data.sources = (data.sources || []).filter(s=>/^https:\/\//i.test(s.url||''));
    const confidence=data.confidence;
    const confidenceText=confidence && Number.isFinite(confidence.score)
      ? `${Math.round(confidence.score*100)}% · ${escape(confidence.level)}. Evidence-quality score, not a probability that a claim is true.`
      : escape(data.evidence_support || (data.sources.length ? 'Source-linked' : 'Live verification unavailable'));
    section.innerHTML = `<header><small>${escape(data.mode || 'ASK FYNURA')}</small>${data.disciplines?`<p>${escape(data.disciplines)}</p>`:''}</header><div class="research-answer">${answerMarkup(data)}</div>${(data.metrics||[]).length?`<div class="research-metrics">${data.metrics.map(m=>`<div><strong>${escape(typeof m.value==='number'?m.value.toLocaleString():m.value)}</strong><span>${escape(m.label)} · ${escape(m.unit)}</span></div>`).join('')}</div>`:''}${data.declined?'':`<details class="answer-confidence"><summary>${confidence?'Evidence confidence':'Evidence support'} · ${confidence?escape(confidence.level):escape(data.evidence_support || (data.sources.length?'Source-linked':'Not live-verified'))}</summary><p>${confidenceText}</p><p>${escape(data.evidence_status||'Inspect source scope, dates and limitations.')}</p>${(confidence?.limitations||data.limitations||[]).map(s=>`<p>${escape(s)}</p>`).join('')}${data.retrieved_at?`<p>Checked ${escape(new Date(data.retrieved_at).toLocaleString())}</p>`:''}</details>`}<details class="research-sources"><summary>Sources (${data.sources.length})</summary>${data.sources.map(s=>`<p><a href="${escape(s.url)}" target="_blank" rel="noopener noreferrer">[${s.id}] ${escape(s.title)}</a>${s.reporting_cutoff?` · Reporting through ${escape(s.reporting_cutoff)}`:''}</p>`).join('')}</details>`;
    if(data.surveillance){const facts=document.createElement('details');facts.innerHTML='<summary>Underlying surveillance evidence</summary>';facts.append(render(data.surveillance));section.append(facts);}
    if(data.brief && window.appendBrief){window.appendBrief(section,data.brief);}
    if(data.followups?.length){const actions=document.createElement('div');actions.className='research-followups';data.followups.forEach(q=>{const button=document.createElement('button');button.type='button';button.textContent=q;button.onclick=()=>researchAsk(q,null);actions.append(button);});section.append(actions);}
    if (data.suggestions) {
      const frame = document.createElement('iframe'); frame.title = 'Google Search suggestions';
      frame.setAttribute('sandbox','allow-popups allow-popups-to-escape-sandbox');
      frame.referrerPolicy = 'no-referrer'; frame.srcdoc = data.suggestions;
      frame.className = 'research-suggestions'; section.append(frame);
    }
    const download = document.createElement('button'); download.type='button'; download.textContent='Download this response and sources';
    download.onclick = () => {
      const text = data.answer + '\n\nSources\n' + data.sources.map(s=>`[${s.id}] ${s.title}: ${s.url}`).join('\n') + '\n\n' + data.evidence_status;
      const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));
      const link=document.createElement('a');link.href=url;link.download='fynura-research-brief.txt';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }; section.append(download);
    return section;
  }
  async function researchAsk(question, providedContext) {
    const input=document.querySelector('#chat-q'), messages=document.querySelector('#messages');
    question=(question||input.value).trim(); if (!question || busy) return;
    if(question.length>1000){toast('Please keep your question under 1,000 characters.');return;}
    const explicit = providedContext !== undefined ? providedContext : document.querySelector('#use-visual-context')?.checked ? intel.context : null;
    setContext(explicit);
    busy=true;
    const send=document.querySelector('#chat-form [aria-label="Send"]'); if(send)send.disabled=true;
    const user=document.createElement('div');user.className='msg user';user.innerHTML=`<span>${escape(question)}</span>`;messages.append(user);
    const status=document.createElement('div');status.className='msg thinking';status.setAttribute('role','status');status.innerHTML='<i>F</i><span>Connecting to Fynura research…</span>';messages.append(status);
    messages.setAttribute('aria-busy','true');messages.scrollTop=messages.scrollHeight;input.value='';
    const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),265000);
    try {
      const response=await fetch('/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,body:JSON.stringify({question,context:explicit,stakeholder_mode:document.querySelector('#stakeholder').value,history})});
      if(!response.ok)throw Error(response.status===401?'Your session expired. Please sign in again.':`Research service unavailable (${response.status}). Please retry.`);
      const reader=response.body.getReader(), decoder=new TextDecoder();let buffer='',answered=false,artifactReceived=false;
      function consume(line){if(!line.trim())return;const event=JSON.parse(line);
        if(event.type==='status')status.querySelector('span').textContent=event.message;
        if(event.type==='error')throw Error(event.message);
        if(event.type==='answer'){
          answered=true;artifactReceived=Boolean(event.data.brief);const row=document.createElement('div');row.className='msg answer';row.innerHTML='<i>F</i>';row.append(render(event.data));messages.append(row);
          if(!event.data.declined && event.data.answer){history.push({question,answer:event.data.answer.slice(0,12000)});if(history.length>8)history.shift();}
        }
      }
      while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let newline;while((newline=buffer.indexOf('\n'))>=0){consume(buffer.slice(0,newline));buffer=buffer.slice(newline+1);}}
      buffer+=decoder.decode();consume(buffer);if(!answered)throw Error('The research connection ended before an answer arrived. Please retry.');
      if (!artifactReceived && /\b(infographic|report brief)\b/i.test(question) && window.appendBrief) {
        status.querySelector('span').textContent='Preparing a separate visual from structured surveillance evidence…';
        try {
          const artifact=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,body:JSON.stringify({question,context:explicit,threat_id:explicit?.threat_id||null,stakeholder_mode:document.querySelector('#stakeholder').value})});
          const data=await artifact.json();
          if(artifact.ok&&data.brief){const section=messages.lastElementChild.querySelector('section');const notice=document.createElement('p');notice.textContent='The downloadable visual below uses the separate structured evidence snapshot, not newly retrieved web estimates.';section.append(notice);window.appendBrief(section,data.brief);}
        } catch (_) { /* The grounded research answer remains available. */ }
      }
    }catch(error){const row=document.createElement('div');row.className='msg';row.innerHTML=`<i>!</i><span>${escape(error.name==='AbortError'?'Research timed out. Please narrow your question and retry.':error.message)}</span>`;messages.append(row);input.value=question;}
    finally{clearTimeout(timer);status.remove();busy=false;if(send)send.disabled=false;messages.setAttribute('aria-busy','false');messages.scrollTop=messages.scrollHeight;}
  }
  window.researchAsk=researchAsk;contextualAsk=researchAsk;ask=researchAsk;
  const form=document.querySelector('#chat-form');
  form.addEventListener('submit',e=>{e.preventDefault();e.stopImmediatePropagation();researchAsk();},true);
  form.addEventListener('click',e=>{if(e.target.closest('[aria-label="Send"]')){e.preventDefault();e.stopImmediatePropagation();researchAsk();}},true);
  form.addEventListener('keydown',e=>{if(e.target.id==='chat-q'&&e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();e.stopImmediatePropagation();researchAsk();}},true);
  const context=document.createElement('label');context.className='research-context';context.innerHTML='<input type="checkbox" id="use-visual-context"> Include the selected visual in my question';form.before(context);
  const reset=document.createElement('button');reset.type='button';reset.textContent='New conversation';reset.style.marginLeft='auto';context.append(reset);
  reset.onclick=()=>{if(busy)return;history.length=0;document.querySelector('#messages').replaceChildren();document.querySelector('#chat-q').value='';document.querySelector('#use-visual-context').checked=false;setContext(null);};
  const intro=document.querySelector('#ask .intro');intro.querySelector('h2').textContent='Ask Fynura. Explore the evidence.';
  intro.querySelector('span').textContent='Live, source-grounded research across public health, with historical context, official guidance and transparent uncertainty. Please do not enter patient-identifying information.';
  document.querySelector('.chathead em').textContent='Live research';
  const greeting=document.querySelector('#messages .msg span');if(greeting)greeting.innerHTML='What would you like to understand? Ask about current threats, historical outbreaks, affected populations or official responses. I will research sources and explain what is known and what remains uncertain.<small>General questions are independent of the selected chart.</small>';
  document.querySelectorAll('.follow button').forEach((button,index)=>{const questions=['What are the current global public-health threats?','Which evidence supports your last answer?','What remains uncertain in your last answer?'];button.onclick=()=>researchAsk(questions[index],null);});
})();
