/* TimLabs studio. Content and navigation are authored as HTML. */
(() => {
  const motion = matchMedia("(prefers-reduced-motion: reduce)");
  const desktop = matchMedia("(min-width: 901px) and (pointer: fine)");
  const hero = document.querySelector(".tl-home-hero");
  const stage = hero?.querySelector(".tl-depth-stage");
  const toggle = hero?.querySelector(".tl-motion-toggle");

  if (stage && toggle && window.TL) {
    let visible = false;
    let moduleLoaded = false;
    let ambientStart = null;
    let last = -Infinity;
    const paused = () => hero.classList.contains("tl-paused") || motion.matches;
    try { hero.classList.toggle("tl-paused",localStorage.getItem("tl-studio-motion") === "paused"); } catch {}
    function ambient(time) {
      if (time-last < (desktop.matches ? 33 : 50)) return;
      last = time;
      if (ambientStart === null) ambientStart = time;
      const elapsed = time-ambientStart;
      stage.style.setProperty("--tl-light-x",`${Math.sin(elapsed/4600)*22}px`);
      stage.style.setProperty("--tl-light-y",`${Math.sin(elapsed/4310)*13}px`);
    }
    function theme() {
      const source = stage.querySelector("source");
      if (!source) return;
      const selected = document.documentElement.dataset.theme;
      source.media = selected === "light" ? "all" : selected === "dark" ? "not all" : "(prefers-color-scheme: light)";
    }
    theme();
    new MutationObserver(theme).observe(document.documentElement,{attributes:true,attributeFilter:["data-theme"]});
    function state() {
      toggle.hidden = motion.matches;
      toggle.setAttribute("aria-pressed",String(hero.classList.contains("tl-paused")));
      if (visible && !paused()) TL.tick.add(ambient); else TL.tick.remove(ambient);
      stage.dispatchEvent(new Event("tl-motion-state"));
      if (!visible || paused() || !desktop.matches || moduleLoaded || navigator.connection?.saveData) return;
      moduleLoaded = true;
      const module = document.createElement("script");
      module.src = stage.dataset.compass;
      document.head.append(module);
    }
    toggle.addEventListener("click",() => {
      hero.classList.toggle("tl-paused");
      try { localStorage.setItem("tl-studio-motion",hero.classList.contains("tl-paused") ? "paused" : "playing"); } catch {}
      state();
    });
    motion.addEventListener("change",state);
    desktop.addEventListener("change",state);
    function watch() {
      new IntersectionObserver(([entry]) => {
        const first = !visible && entry.isIntersecting;
        visible = entry.isIntersecting;
        if (first && !paused() && !stage.dataset.entered) {
          const art = stage.querySelector("picture");
          stage.dataset.entered = "1";
          art?.animate([{transform:"translateY(18px) scale(.92)"},{transform:"none"}],{
            duration:720,easing:"cubic-bezier(.23,1,.32,1)"
          });
        }
        state();
      }).observe(stage);
    }
    // Let the headline and responsive poster finish their first paint.
    const afterLoad = () => {
      if ("requestIdleCallback" in window) requestIdleCallback(watch,{timeout:800});
      else setTimeout(watch,100);
    };
    if (document.readyState === "complete") afterLoad();
    else window.addEventListener("load",afterLoad,{once:true});
    state();
  }

  if (window.TL && !motion.matches) {
    const services = [...document.querySelectorAll(".tl-service-grid .tl-service")];
    TL.Inview(".tl-service-grid",{onEnter() {
      if (hero?.classList.contains("tl-paused")) return;
      services.forEach((card,index) => card.animate(
        [{transform:`translateY(${18+index*5}px) rotateX(11deg) scale(.98)`},{transform:"none"}],
        {duration:650,delay:index*60,easing:"cubic-bezier(.23,1,.32,1)"}
      ));
    }});
    if (desktop.matches) services.forEach(card => {
      card.addEventListener("pointermove",event => {
        if (motion.matches || hero?.classList.contains("tl-paused")) return;
        const rect = card.getBoundingClientRect();
        card.style.setProperty("--tl-x",`${(0.5-(event.clientY-rect.top)/rect.height)*4}deg`);
        card.style.setProperty("--tl-y",`${((event.clientX-rect.left)/rect.width-0.5)*5}deg`);
      },{passive:true});
      card.addEventListener("pointerleave",() => {
        card.style.removeProperty("--tl-x");
        card.style.removeProperty("--tl-y");
      });
    });
    TL.Inview(".tl-book-shelf",{onEnter(shelf) {
      shelf.querySelectorAll(".tl-book-volume").forEach((book,index) => {
        const finish = getComputedStyle(book).transform;
        book.animate([{transform:"translateY(23px) rotateY(-38deg) scale(.94)"},{transform:finish}],{
          duration:740,delay:index*75,easing:"cubic-bezier(.23,1,.32,1)"
        });
      });
    }});
  }

  const list = document.querySelector(".tl-project-list");
  if (list) {
    const controls = document.querySelector(".tl-project-controls");
    const [prev,next] = controls.querySelectorAll("button");
    const items = [...list.children];
    const smooth = () => !motion.matches && !hero?.classList.contains("tl-paused");
    const edge = () => list.scrollWidth-list.clientWidth;
    function sync() {
      prev.disabled = list.scrollLeft < 2;
      next.disabled = list.scrollLeft >= edge()-2;
      items.forEach(item => {
        const delta = (item.offsetLeft-list.scrollLeft)/Math.max(1,list.clientWidth);
        item.style.setProperty("--tl-project-turn",smooth() ? `${Math.max(-8, Math.min(9,delta*15))}deg` : "0deg");
      });
    }
    function step(direction) {
      const stops = items.map(item => Math.min(edge(),item.offsetLeft-items[0].offsetLeft));
      const current = list.scrollLeft;
      const target = direction > 0
        ? stops.find(left => left > current+3) ?? edge()
        : stops.findLast(left => left < current-3) ?? 0;
      list.scrollTo({left:target,behavior:smooth() ? "smooth" : "instant"});
    }
    prev.addEventListener("click",() => step(-1));
    next.addEventListener("click",() => step(1));
    list.addEventListener("keydown",event => {
      if (event.target !== list || !["ArrowLeft","ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      step(event.key === "ArrowRight" ? 1 : -1);
    });
    list.addEventListener("scroll",sync,{passive:true});
    motion.addEventListener("change",sync);
    new ResizeObserver(sync).observe(list);
    list.querySelectorAll("img").forEach(img => { img.draggable = false; });
    let gesture;
    let blockClick = false;
    list.addEventListener("pointerdown",event => {
      if (event.pointerType !== "mouse" || event.button !== 0) return;
      gesture = {x:event.clientX,left:list.scrollLeft,id:event.pointerId};
      blockClick = false;
    });
    list.addEventListener("pointermove",event => {
      if (!gesture || event.pointerId !== gesture.id) return;
      const dx = event.clientX-gesture.x;
      if (!blockClick && Math.abs(dx) < 8) return;
      if (!blockClick) list.setPointerCapture(event.pointerId);
      blockClick = true;
      list.classList.add("tl-dragging");
      list.scrollLeft = gesture.left-dx;
    });
    for (const type of ["pointerup","pointercancel","lostpointercapture","pointerleave"]) list.addEventListener(type,() => {
      if (type === "pointerleave" && blockClick) return;
      gesture = null;
      list.classList.remove("tl-dragging");
    });
    list.addEventListener("click",event => {
      if (!blockClick || event.detail === 0) return;
      blockClick = false;
      event.preventDefault();
      event.stopPropagation();
    },true);
    controls.hidden = false;
    sync();
  }

  if (document.body.classList.contains("shop")) {
    document.addEventListener("tl-cart-added",event => {
      if (motion.matches) return;
      const surface = event.target.closest(".sh-buy");
      if (!surface) return;
      surface.querySelectorAll(".tl-cart-spark").forEach(spark => spark.remove());
      for (let i=0; i<7; i++) {
        const spark = document.createElement("span");
        spark.className = "tl-cart-spark";
        spark.setAttribute("aria-hidden","true");
        surface.append(spark);
        const angle = (i/6)*Math.PI + Math.PI;
        const distance = 28 + i%3*8;
        const burst = spark.animate([
          {opacity:.85,transform:`rotate(${angle}rad) scale(.55)`},
          {opacity:0,transform:`translate(${Math.cos(angle)*distance}px,${Math.sin(angle)*distance}px) rotate(${angle}rad) scale(.17)`}
        ],{duration:380,easing:"cubic-bezier(.1,.7,.22,1)"});
        burst.onfinish = () => spark.remove();
      }
    });
  }
})();
