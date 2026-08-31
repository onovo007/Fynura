const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function setup({unsupported=false,throws=false}={}){
  const elements=[];
  function element(){const node={dataset:{},attributes:{},listeners:{},classList:{add(){},remove(){}},span:{},value:'old question',setAttribute(k,v){this.attributes[k]=v},addEventListener(k,v){this.listeners[k]=v},querySelector(){return this.span},dispatchEvent(){},insertBefore(child){elements.push(child)},insertAdjacentElement(_,child){elements.push(child)}};return node;}
  const form=element(),input=element();let rec;
  class Recognition{constructor(){rec=this}start(){if(throws)throw Error('start failed')}stop(){this.onend()}abort(){}}
  const context={window:{isSecureContext:true,SpeechRecognition:unsupported?undefined:Recognition,addEventListener(){}},navigator:{language:'en-US'},document:{readyState:'complete',documentElement:{},createElement:element,querySelector:s=>s==='#chat-form'?form:input,querySelectorAll:()=>[]},MutationObserver:class{observe(){}},Event:class{},console};
  vm.runInNewContext(fs.readFileSync('frontend/voice.js','utf8'),context);
  return {mic:elements[0],status:elements[1],input,click:()=>elements[0].listeners.click({preventDefault(){},stopImmediatePropagation(){}}),rec:()=>rec};
}
let x=setup();assert.equal(x.mic.dataset.ready,'true');x.click();x.rec().onstart();assert.equal(x.mic.attributes['aria-pressed'],'true');
x.rec().onerror({error:'not-allowed'});x.rec().onend();assert.match(x.status.textContent,/denied/);assert.equal(x.input.value,'old question');
x=setup();x.click();x.rec().onresult({results:[[{transcript:'new public health question'}]]});x.rec().onend();assert.equal(x.input.value,'new public health question');assert.match(x.status.textContent,/select Send/);
x=setup({throws:true});x.click();assert.match(x.status.textContent,/could not start/);assert.equal(x.mic.disabled,false);
x=setup({unsupported:true});assert.equal(x.mic.disabled,true);assert.match(x.status.textContent,/unavailable/);
for(const code of ['network','audio-capture','no-speech','aborted']){x=setup();x.click();x.rec().onerror({error:code});const message=x.status.textContent;x.rec().onend();assert.equal(x.status.textContent,message);}
console.log('Voice checks passed: activation, permission denial, start failure, no-speech/network/device errors, transcript review, no automatic submission.');
