(() => {
  const hero=document.querySelector('#top');
  if(!hero)return;
  const panel=document.createElement('section');
  panel.className='entry-story';
  panel.setAttribute('aria-label','From evidence to public-health understanding');
  panel.innerHTML='<div class="story-image story-map" aria-hidden="true"></div><div class="story-image story-analysis" aria-hidden="true"></div><div class="story-image story-communities" aria-hidden="true"></div><div class="story-copy"><small>FROM SIGNAL TO UNDERSTANDING</small><h2>Evidence connects us.</h2><p>Fynura transforms fragmented outbreak surveillance into evidence-grounded global public-health intelligence.</p><p>Discover emerging signals. Compare authoritative evidence. Explore outbreaks geographically. Ask questions. Understand what changed.</p><p>WHO · Africa CDC · ECDC · PAHO · CDC · National Health Authorities</p><a href="#signals">Explore global intelligence →</a><p><small class="story-disclaimer">Illustrative imagery · surveillance intelligence shown elsewhere uses verified evidence.</small></p></div><button type="button" class="story-pause" aria-pressed="false">Pause imagery</button>';
  const activate=()=>{panel.classList.add('story-loaded');observer.disconnect()};
  hero.after(panel);
  const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting))activate()},{rootMargin:'120px'});
  observer.observe(panel);
  panel.querySelector('button').onclick=e=>{const paused=panel.classList.toggle('story-paused');e.currentTarget.textContent=paused?'Resume imagery':'Pause imagery';e.currentTarget.setAttribute('aria-pressed',String(paused))};
})();
