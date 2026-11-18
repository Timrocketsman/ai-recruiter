/* Scroll-driven perspective. Older browsers use the shared site frame. */
(() => {
  const field = document.querySelector("body > .tl-space");
  if (!field || !CSS.supports("mask-image","linear-gradient(black,black)")) return;
  const key = "tl-studio-motion";
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const data = navigator.connection;
  const studio = field.dataset.tone === "studio";
  const hero = document.querySelector(".tl-home-hero");
  const control = hero?.querySelector(".tl-motion-toggle") || document.querySelector(".tl-space-control");
  const planes = [field.querySelector(".tl-space-far"),field.querySelector(".tl-space-format")];
  const travel = [
    "translate3d(clamp(-10px,-.8vw,-4px),clamp(-30px,-2.4vw,-13px),0) scale(1.035)",
    "translate3d(clamp(-28px,-2vw,-12px),clamp(-68px,-5vw,-29px),0) scale(1.09)"
  ];
  const supported = typeof ScrollTimeline === "function" && "rangeEnd" in Animation.prototype;
  let tick;
  let tracks = [];
  let listening = false;
  function drawScroll() {
    tick.remove(drawScroll);
    if (!listening) return;
    const progress = 1 - (1 - Math.min(1,Math.max(0,scrollY)/1100))**2;
    const vw = innerWidth * .01;
    const span = (rate,min,max) => Math.min(max,Math.max(min,rate*vw));
    [[span(.8,4,10),span(2.4,13,30),.035],
     [span(2,12,28),span(5,29,68),.09]].forEach(([x,y,s],i)=>{
      planes[i].style.transform = `translate3d(${-x*progress}px,${-y*progress}px,0) scale(${1+s*progress})`;
    });
  }
  const onScroll = () => tick.add(drawScroll);
  function fallback(active) {
    if (active === listening) return;
    listening = active;
    if (active) {
      addEventListener("scroll",onScroll,{passive:true});
      onScroll();
    } else {
      removeEventListener("scroll",onScroll);
      tick.remove(drawScroll);
    }
  }
  let loaded = false;
  let paused = false;

  function read() {
    try { paused = localStorage.getItem(key) === "paused"; } catch {}
  }
  function sync() {
    if (!loaded) return;
    const draw = !data?.saveData;
    const animate = studio && (supported || !!tick) && draw && !reduce.matches;
    if (!supported) fallback(animate && !paused);
    field.classList.toggle("tl-space-ready",draw);
    if (!hero && control) {
      control.hidden = !animate;
      control.setAttribute("aria-pressed",String(paused));
    }
    if (!animate || paused) {
      const freeze = animate && paused && tracks.length;
      const transforms = freeze ? planes.map(plane=>getComputedStyle(plane).transform) : [];
      tracks.forEach(track=>track.cancel());
      tracks = [];
      if (!animate) planes.forEach(plane=>plane.style.removeProperty("transform"));
      if (freeze) planes.forEach((plane,i)=>{plane.style.transform=transforms[i];});
      return;
    }
    if (!supported || tracks.length) return;
    const timeline = new ScrollTimeline({source:document.scrollingElement,axis:"block"});
    tracks = planes.map((plane,i)=>{
      plane.style.removeProperty("transform");
      return plane.animate(
        [{transform:"translate3d(0,0,0) scale(1)"},{transform:travel[i]}],
        {timeline,duration:"auto",rangeEnd:"1100px",fill:"both",easing:"cubic-bezier(.21,.55,.43,1)"}
      );
    });
  }

  if (hero && control) {
    new MutationObserver(()=>{
      paused = hero.classList.contains("tl-paused");
      sync();
    }).observe(hero,{attributes:true,attributeFilter:["class"]});
  } else control?.addEventListener("click",()=>{
    paused = !paused;
    try { localStorage.setItem(key,paused ? "paused" : "playing"); } catch {}
    sync();
  });
  reduce.addEventListener("change",sync);
  data?.addEventListener?.("change",sync);
  addEventListener("pageshow",()=>{read();sync();});
  addEventListener("storage",event=>{if (event.key === key) {read();sync();}});
  const init = () => {
    const start = ()=>{tick=window.TL?.tick;read();loaded=true;sync();};
    if ("requestIdleCallback" in window) requestIdleCallback(start,{timeout:900});
    else setTimeout(start,120);
  };
  if (document.readyState === "complete") init();
  else addEventListener("load",init,{once:true});
})();
