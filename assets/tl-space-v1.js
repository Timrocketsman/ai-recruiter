/* Ambient movement uses compositor transforms. No frame polling or canvas. */
(() => {
  const field = document.querySelector("body > .tl-space");
  if (!field || typeof field.animate!=="function") return;
  const layers = [...field.children];
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const slowData = navigator.connection;
  const key = "tl-studio-motion";
  let loaded = false;
  let stopped = false;
  let animations = [];
  try { stopped = localStorage.getItem(key)==="paused"; } catch {}
  const home = document.querySelector(".tl-home-hero");
  const control = home?.querySelector(".tl-motion-toggle") || document.querySelector(".tl-space-control");
  const tracks = [
    {time:29000,frames:["translate3d(-2%,1%,0) scale(1.01)","translate3d(3%,-2%,0) scale(1.06)"]},
    {time:36000,frames:["translate3d(2%,-2%,0) scale(1.01)","translate3d(-3%,3%,0) scale(1.08)"]},
    {time:21000,frames:["translate3d(-2%,3%,0) scale(1.03)","translate3d(3%,-4%,0) scale(1.11)"]}
  ];
  function settings() {
    if (control && !home) {
      control.hidden = reduce.matches;
      control.setAttribute("aria-pressed",String(stopped));
    }
    if (!loaded) return;
    if (reduce.matches || stopped || slowData?.saveData) {
      animations.forEach(animation=>animation.cancel());
      animations = [];
      resetDepth();
      return;
    }
    if (document.hidden) {
      animations.forEach(animation=>animation.pause());
      return;
    }
    if (!animations.length) {
      animations = tracks.map((track,i)=>{
        const motion = layers[i].animate(track.frames.map(transform=>({transform})),
          {duration:track.time,direction:"alternate",iterations:Infinity,easing:"ease-in-out"});
        const now = performance.timeOrigin+performance.now();
        motion.currentTime = now%(track.time*2);
        return motion;
      });
    } else animations.forEach(animation=>animation.play());
  }
  function resetDepth() {
    field.style.removeProperty("--tl-depth-x");
    field.style.removeProperty("--tl-depth-y");
  }
  const fine = matchMedia("(hover: hover) and (pointer: fine)");
  if (field.dataset.tone==="studio") {
    let lastMove = 0;
    addEventListener("pointermove",event=>{
      if (!loaded || stopped || reduce.matches || slowData?.saveData || !fine.matches ||
          event.pointerType!=="mouse" || event.timeStamp-lastMove<85) return;
      lastMove = event.timeStamp;
      field.style.setProperty("--tl-depth-x",`${((event.clientX/innerWidth-.5)*32).toFixed(1)}px`);
      field.style.setProperty("--tl-depth-y",`${((event.clientY/innerHeight-.5)*25).toFixed(1)}px`);
    },{passive:true});
    document.documentElement.addEventListener("pointerleave",resetDepth);
  }
  function syncPreference() {
    try { stopped = localStorage.getItem(key)==="paused"; } catch {}
    settings();
  }
  function start() {
    if (loaded) return;
    loaded = true;
    if (!slowData?.saveData) field.classList.add("tl-space-ready");
    settings();
  }
  const deferStart = () => {
    if ("requestIdleCallback" in window) requestIdleCallback(start,{timeout:850});
    else setTimeout(start,120);
  };
  if (home && control) {
    new MutationObserver(()=>{
      stopped = home.classList.contains("tl-paused");
      settings();
    }).observe(home,{attributes:true,attributeFilter:["class"]});
  } else control?.addEventListener("click",()=>{
    stopped = !stopped;
    try { localStorage.setItem(key,stopped?"paused":"playing"); } catch {}
    settings();
  });
  reduce.addEventListener("change",settings);
  slowData?.addEventListener?.("change",settings);
  document.addEventListener("visibilitychange",settings);
  addEventListener("pageshow",syncPreference);
  addEventListener("storage",event=>{if (event.key===key) syncPreference();});
  if (document.readyState==="complete") deferStart();
  else addEventListener("load",deferStart,{once:true});
  settings();
})();
