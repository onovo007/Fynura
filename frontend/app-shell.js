(() => {
  const workspaces = {
    monitor: {title:'Monitor verified public-health signals',summary:'Explore current surveillance, compatible indicators, country coverage and threat trajectories.',sections:['signals','threats','canonical-table','visuals','nigeria-availability']},
    verify: {title:'Verify the evidence behind every claim',summary:'Inspect sources, provenance, reporting periods, harmonization rules and evidence limitations.',sections:['sources','harmonization']},
    detect: {title:'Review historical patterns and early signals',summary:'Examine descriptive history and eligible statistical screening without treating signals as forecasts.',sections:['historical-evidence']},
    advise: {title:'Ask Fynura and create evidence-grounded outputs',summary:'Ask scientific or surveillance questions, review citations, and generate briefs or infographics.',sections:['ask']},
    learn: {title:'Understand methods, coverage and responsible use',summary:'Review system boundaries, source availability, methodology and reproducibility resources.',sections:['fynura-story','trust']}
  };
  const aliases={signals:'monitor',visuals:'monitor',sources:'verify','historical-evidence':'detect',ask:'advise',trust:'learn'};
  const valid=value=>Object.prototype.hasOwnProperty.call(workspaces,value);
  const route=()=>{const name=location.pathname.split('/').filter(Boolean)[0];return valid(name)?name:aliases[location.hash.slice(1)]||'monitor'};
  let active=route();
  function masthead(){let node=document.querySelector('#workspace-masthead');if(node)return node;node=document.createElement('section');node.id='workspace-masthead';node.className='workspace-masthead';node.setAttribute('aria-live','polite');document.querySelector('main')?.prepend(node);return node}
  function identify(){document.querySelectorAll('main > section').forEach(section=>{if(section.id==='workspace-masthead')return;if(!section.id&&section.classList.contains('threats'))section.dataset.shellSection='threats';else if(section.id)section.dataset.shellSection=section.id})}
  function render({focus=false}={}){identify();document.body.dataset.workspace=active;const spec=workspaces[active],head=masthead();head.innerHTML=`<p>${active.toUpperCase()} WORKSPACE</p><h1>${spec.title}</h1><span>${spec.summary}</span>`;document.querySelectorAll('main > section[data-shell-section]').forEach(section=>{const visible=spec.sections.includes(section.dataset.shellSection);section.hidden=!visible;section.setAttribute('aria-hidden',String(!visible))});document.querySelectorAll('[data-workspace-link]').forEach(link=>{const selected=link.dataset.workspaceLink===active;link.classList.toggle('active',selected);selected?link.setAttribute('aria-current','page'):link.removeAttribute('aria-current');link.href=`/${link.dataset.workspaceLink}${location.search}`});document.title=`Fynura · ${active[0].toUpperCase()+active.slice(1)}`;const ask=document.querySelector('#ask-fynura-launcher');if(ask)ask.hidden=active==='advise';if(focus){head.tabIndex=-1;head.focus({preventScroll:true});scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}}
  function navigate(name,{replace=false}={}){if(!valid(name))return;active=name;history[replace?'replaceState':'pushState']({workspace:name},'',`/${name}${location.search}`);render({focus:!replace})}
  function addLauncher(){if(document.querySelector('#ask-fynura-launcher'))return;const button=document.createElement('button');button.id='ask-fynura-launcher';button.className='ask-fynura-launcher';button.type='button';button.innerHTML='<i>F</i><span>Ask Fynura</span>';button.setAttribute('aria-label','Open the Ask Fynura workspace');button.onclick=()=>navigate('advise');document.body.append(button)}
  document.addEventListener('click',event=>{const link=event.target.closest('[data-workspace-link]');if(!link||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();navigate(link.dataset.workspaceLink)});
  addEventListener('popstate',()=>{active=route();render({focus:true})});
  addEventListener('hashchange',()=>{const target=aliases[location.hash.slice(1)];if(target)navigate(target,{replace:true})});
  const observer=new MutationObserver(()=>render());
  function start(){if(location.pathname==='/'||aliases[location.hash.slice(1)])navigate(route(),{replace:true});addLauncher();render();const main=document.querySelector('main');if(main)observer.observe(main,{childList:true})}
  document.readyState==='loading'?addEventListener('DOMContentLoaded',start):start();
})();
