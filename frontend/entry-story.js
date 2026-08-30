(() => {
  const hero=document.querySelector('#top');if(!hero)return;
  const styles=document.createElement('link');styles.rel='stylesheet';styles.href='/static/entry-sequence.css?v=2';document.head.append(styles);
  const frames=[
    ['surveillance','See the signal sooner.','Global public-health intelligence from authoritative evidence.'],
    ['analysis','Turn fragmented surveillance into intelligence.','Fynura discovers, verifies and connects evidence across authoritative sources.'],
    ['protection','From evidence to public-health action.','Understand what is changing, where it is changing and how strong the supporting evidence is.'],
    ['map','See where signals are emerging.','Explore verified surveillance geographically across diseases, countries and regions.'],
    ['communities','Intelligence for the communities we serve.','Evidence made understandable for the public, researchers, clinicians, journalists and decision-makers.']
  ];
  const panel=document.createElement('section');panel.id='fynura-story';panel.className='entry-story cinematic-story';panel.setAttribute('aria-label','From evidence to public-health understanding');
  panel.innerHTML='<div class="story-identity"><strong>FYNURA</strong><span>Global public-health intelligence</span></div>'+frames.map(([asset,title,copy],i)=>'<div class="story-frame '+(i===0?'is-active':'')+'" aria-hidden="'+(i!==0)+'"><div class="story-image story-'+asset+'"></div><div class="story-copy"><small>0'+(i+1)+' / SIGNAL TO UNDERSTANDING</small><h2>'+title+'</h2><p>'+copy+'</p></div></div>').join('')+'<div class="story-footer"><a href="#signals">Explore intelligence →</a><small>Illustrative photography, not live surveillance data.</small><div class="story-controls"><span class="story-count">1 / 5</span><button type="button" class="story-pause" aria-pressed="false">Pause imagery</button><button type="button" class="story-next" aria-label="Next story frame">Next →</button></div></div>';
  hero.after(panel);
  const motion=matchMedia('(prefers-reduced-motion: reduce)');let active=0,paused=false,visible=false,timer;
  const schedule=()=>{clearTimeout(timer);if(visible&&!paused&&!motion.matches&&!document.hidden)timer=setTimeout(()=>{advance();schedule()},10000)};
  function advance(){const nodes=panel.querySelectorAll('.story-frame');nodes[active].classList.remove('is-active');nodes[active].setAttribute('aria-hidden','true');active=(active+1)%frames.length;nodes[active].classList.add('is-active');nodes[active].setAttribute('aria-hidden','false');panel.querySelector('.story-count').textContent=(active+1)+' / '+frames.length}
  const observer=new IntersectionObserver(entries=>{visible=entries.some(e=>e.isIntersecting);if(visible)panel.classList.add('story-loaded');schedule()},{rootMargin:'120px'});observer.observe(panel);
  panel.querySelector('.story-pause').onclick=e=>{paused=!paused;e.currentTarget.textContent=paused?'Resume imagery':'Pause imagery';e.currentTarget.setAttribute('aria-pressed',String(paused));schedule()};
  panel.querySelector('.story-next').onclick=()=>{advance();schedule()};
  motion.addEventListener('change',schedule);document.addEventListener('visibilitychange',schedule);
})();
