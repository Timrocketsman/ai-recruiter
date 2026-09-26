/* TimLabs · эффекты карточек: появление при прокрутке и блик за курсором. ~1 КБ, без библиотек. */
(function(){
  var d=document,reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var rv=d.querySelectorAll('.rv');
  if('IntersectionObserver' in window && !reduce){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{rootMargin:'0px 0px -8% 0px'});
    rv.forEach(function(el,i){el.style.transitionDelay=(i%4)*60+'ms';io.observe(el);});
  } else rv.forEach(function(el){el.classList.add('in');});
  if(reduce||!matchMedia('(hover: hover)').matches) return;
  var raf=0,card=null,ev=null;
  d.addEventListener('pointermove',function(e){
    card=e.target.closest&&e.target.closest('.gcard');ev=e;
    if(card&&!raf) raf=requestAnimationFrame(function(){raf=0;if(!card)return;
      var r=card.getBoundingClientRect();
      card.style.setProperty('--mx',(ev.clientX-r.left)+'px');
      card.style.setProperty('--my',(ev.clientY-r.top)+'px');});
  },{passive:true});
})();
