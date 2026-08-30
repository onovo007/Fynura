(() => {
  const hero=document.querySelector('#top');
  if(!hero)return;
  const panel=document.createElement('section');
  panel.className='entry-story';
  panel.setAttribute('aria-label','From evidence to public-health understanding');
  panel.innerHTML='<div class="story-image story-analysis" aria-hidden="true"></div><div class="story-image story-communities" aria-hidden="true"></div><div class="story-copy"><small>FROM SIGNAL TO UNDERSTANDING</small><h2>Evidence connects us.</h2><p>Authoritative sources. Shared understanding.<br>Intelligence for the communities we serve.</p><small class="story-disclaimer">Illustrative photography · not live surveillance data</small></div><button type="button" class="story-pause" aria-pressed="false">Pause imagery</button>';
  const activate=()=>{panel.classList.add('story-loaded');observer.disconnect()};
  hero.after(panel);
  const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting))activate()},{rootMargin:'120px'});
  observer.observe(panel);
  panel.querySelector('button').onclick=e=>{const paused=panel.classList.toggle('story-paused');e.currentTarget.textContent=paused?'Resume imagery':'Pause imagery';e.currentTarget.setAttribute('aria-pressed',String(paused))};
})();
