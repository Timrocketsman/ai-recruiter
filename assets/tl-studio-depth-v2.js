/* TimLabs studio. Content and navigation are authored as HTML. */
(() => {
  const motion = matchMedia("(prefers-reduced-motion: reduce)");
  const desktop = matchMedia("(min-width: 901px) and (pointer: fine)");
  const hero = document.querySelector(".tl-home-hero");
  const stage = hero?.querySelector(".tl-depth-stage");
  const toggle = hero?.querySelector(".tl-motion-toggle");
  const portal = stage?.querySelector(".tl-portal-preview");
  const portalLink = stage?.querySelector(".tl-portal-link");

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
      if (visible && !paused() && !stage.classList.contains("tl-portal-open")) TL.tick.add(ambient);
      else TL.tick.remove(ambient);
      stage.dispatchEvent(new Event("tl-motion-state"));
      if (!visible || paused() || !desktop.matches || moduleLoaded || navigator.connection?.saveData) return;
      moduleLoaded = true;
      const module = document.createElement("script");
      module.src = stage.dataset.compass;
      document.head.append(module);
    }
    if (portal && portalLink) {
      let imageReady;
      let requested = false;
      let previewedOnScroll = false;
      let previewOnHover = false;
      let previewOnFocus = false;

      function loadPreview() {
        if (!imageReady) {
          imageReady = new Promise(resolve => {
            const img = new Image();
            img.alt = "";
            img.decoding = "async";
            img.fetchPriority = "low";
            img.width = 960;
            img.height = 680;
            img.onload = () => { portal.append(img); resolve(true); };
            img.onerror = () => resolve(false);
            img.src = portal.dataset.image;
          });
        }
        return imageReady;
      }

      function showPreview(open) {
        requested = open;
        if (!open) {
          if (stage.classList.contains("tl-portal-open")) {
            stage.classList.remove("tl-portal-open");
            state();
          }
          return;
        }
        loadPreview().then(ready => {
          if (!ready || !requested || document.hidden) return;
          stage.classList.add("tl-portal-open");
          state();
        });
      }

      portalLink.addEventListener("pointerenter", event => {
        if (event.pointerType !== "mouse" || paused()) return;
        previewOnHover = true;
        showPreview(true);
      });
      portalLink.addEventListener("pointerleave", () => {
        previewOnHover = false;
        if (!previewOnFocus) showPreview(false);
      });
      portalLink.addEventListener("focus", () => {
        previewOnFocus = true;
        if (!motion.matches) showPreview(true);
      });
      portalLink.addEventListener("blur", () => {
        previewOnFocus = false;
        if (!previewOnHover) showPreview(false);
      });
      portalLink.addEventListener("keydown", event => {
        if (event.key === "Escape") showPreview(false);
      });

      function scrollPreview() {
        if (scrollY < 42 || paused() || document.hidden || navigator.connection?.saveData) return;
        const bounds = stage.getBoundingClientRect();
        const visibleHeight = Math.min(bounds.bottom, innerHeight) - Math.max(bounds.top, 0);
        if (visibleHeight < bounds.height * .72) return;
        previewedOnScroll = true;
        removeEventListener("scroll", scrollPreview);
        showPreview(true);
      }
      addEventListener("scroll", scrollPreview, {passive:true});
      new IntersectionObserver(([entry]) => {
        if (!entry.isIntersecting && previewedOnScroll && !previewOnFocus) showPreview(false);
      }).observe(stage);
      motion.addEventListener("change", () => {
        if (motion.matches) showPreview(false);
      });
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
    const services = [...document.querySelectorAll(".tl-service-grid:not(.tl-rail-scroll) .tl-service")];
    TL.Inview(".tl-service-grid:not(.tl-rail-scroll)",{onEnter() {
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
  }

  const railMotion = () => !motion.matches && !hero?.classList.contains("tl-paused");

  function stepRail(list, direction, wrap) {
    const edge = list.scrollWidth - list.clientWidth;
    const items = [...list.children];
    if (!items.length || edge < 2) return;
    const stops = items.map(item => Math.min(edge, item.offsetLeft - items[0].offsetLeft));
    const current = list.scrollLeft;
    const stop = direction > 0
      ? stops.find(left => left > current + 3)
      : stops.findLast(left => left < current - 3);
    const atEdge = direction > 0 ? current >= edge - 3 : current <= 3;
    const target = stop ?? (wrap && atEdge ? (direction > 0 ? 0 : edge) : (direction > 0 ? edge : 0));
    list.scrollTo({left:target,behavior:railMotion() && !(wrap && atEdge) ? "smooth" : "instant"});
  }

  function bindRail(list, wrap = false) {
    list.addEventListener("keydown", event => {
      if (event.target !== list || event.altKey || event.ctrlKey || event.metaKey) return;
      const step = {ArrowLeft:-1,ArrowRight:1}[event.key];
      if (step) {
        event.preventDefault();
        stepRail(list, step, wrap);
      } else if (wrap && (event.key === "Home" || event.key === "End")) {
        event.preventDefault();
        list.scrollTo({left:event.key === "Home" ? 0 : list.scrollWidth,behavior:"instant"});
      }
    });
    list.querySelectorAll("img").forEach(image => { image.draggable = false; });
    let gesture;
    let blockClick = false;

    list.addEventListener("pointerdown", event => {
      if (event.pointerType !== "mouse" || event.button !== 0 || event.target.closest(".g-depth,input,select,textarea")) return;
      gesture = {x:event.clientX,y:event.clientY,left:list.scrollLeft,id:event.pointerId};
      blockClick = false;
    });
    list.addEventListener("pointermove", event => {
      if (!gesture || event.pointerId !== gesture.id) return;
      const dx = event.clientX - gesture.x;
      if (!blockClick) {
        if (Math.abs(event.clientY - gesture.y) > Math.abs(dx) + 8) { gesture = null; return; }
        if (Math.abs(dx) < 8) return;
        list.setPointerCapture(event.pointerId);
      }
      blockClick = true;
      list.classList.add("tl-dragging");
      list.scrollLeft = gesture.left - dx;
    });
    for (const type of ["pointerup","pointercancel","lostpointercapture","pointerleave"]) list.addEventListener(type, () => {
      if (type === "pointerleave" && blockClick) return;
      gesture = null;
      list.classList.remove("tl-dragging");
    });
    list.addEventListener("click", event => {
      if (!blockClick || event.detail === 0) return;
      blockClick = false;
      event.preventDefault();
      event.stopPropagation();
    }, true);
  }

  for (const list of document.querySelectorAll(".tl-project-list")) {
    const controls = list.closest(".tl-projects").querySelector(".tl-project-controls");
    const [prev,next] = controls.querySelectorAll("button");
    const items = [...list.children];
    function sync() {
      prev.disabled = list.scrollLeft < 2;
      next.disabled = list.scrollLeft >= list.scrollWidth - list.clientWidth - 2;
      items.forEach(item => {
        const delta = (item.offsetLeft - list.scrollLeft) / Math.max(1, list.clientWidth);
        item.style.setProperty("--tl-project-turn",railMotion() ? Math.max(-8, Math.min(9,delta*15)) + "deg" : "0deg");
      });
    }
    prev.addEventListener("click", () => stepRail(list, -1, false));
    next.addEventListener("click", () => stepRail(list, 1, false));
    list.addEventListener("scroll", sync, {passive:true});
    motion.addEventListener("change", sync);
    new ResizeObserver(sync).observe(list);
    bindRail(list);
    controls.hidden = false;
    sync();
  }

  const projects = document.querySelector("#tl-mine-list");
  if (projects) {
    bindRail(projects, true);
    const scene = projects.closest(".tl-arc-scene");
    const section = scene?.closest("#moi");
    const beam = scene?.querySelector(".tl-arc-beam");
    if (section && beam) {
      // Keep reading and focus order aligned whenever the showcase generator refreshes the cards.
      const school = projects.querySelector("#card-school");
      const music = projects.querySelector("#card-music");
      if (school && music) projects.insertBefore(school, music);
      const cards = Array.from(projects.querySelectorAll(":scope>article"));
      const tags = Array.from(section.querySelectorAll(".tl-arc-tags a"));
      let geometry = [], stops = [], frame = 0, viewport = 0, visible = false, drift, flash;

      function paint() {
        frame = 0;
        if (!visible || !geometry.length) return;
        const left = projects.scrollLeft;
        const middle = viewport / 2;
        const moving = railMotion();
        const closest = stops.reduce((best, stop, index) => Math.abs(stop-left) < Math.abs(stops[best]-left) ? index : best, 0);
        tags.forEach((tag, index) => {
          if (index === closest) tag.setAttribute("aria-current", "true");
          else tag.removeAttribute("aria-current");
        });
        cards.forEach((card,index) => {
          const projected = (geometry[index] - left - middle) / Math.max(1,middle);
          const d = moving ? Math.max(-1, Math.min(1, projected)) : 0;
          const bend = 1 - Math.cos(d * 1.14);
          const small = viewport < 650;
          card.style.setProperty("--arc-y", (bend * (small ? 25 : 61)).toFixed(2) + "px");
          card.style.setProperty("--arc-z", (-bend * (small ? 15 : 52)).toFixed(2) + "px");
          card.style.setProperty("--arc-yaw", (-d * (small ? 5 : 12)).toFixed(2) + "deg");
          card.style.setProperty("--arc-bank", (d * (small ? 2 : 4.5)).toFixed(2) + "deg");
        });
      }

      function schedule() {
        if (visible && !frame) frame = requestAnimationFrame(paint);
      }

      function measure() {
        viewport = projects.clientWidth;
        geometry = cards.map(card => card.offsetLeft + card.offsetWidth / 2);
        const limit = Math.max(0, projects.scrollWidth - viewport);
        const first = cards[0]?.offsetLeft ?? 0;
        stops = tags.map(tag => Math.max(0, Math.min(limit, (projects.querySelector(tag.hash)?.offsetLeft ?? first) - first)));
        schedule();
      }

      function sync() {
        const moving = railMotion() && visible && !document.hidden;
        scene.toggleAttribute("data-arc-motion", moving);
        if (moving) {
          drift ??= beam.animate?.([{transform:"translate3d(-2%,1%,0)"},{transform:"translate3d(3%,-2%,0)"}],
            {duration:17000,direction:"alternate",iterations:Infinity,easing:"ease-in-out"});
          drift?.play();
        } else drift?.pause();
        schedule();
      }

      if ("IntersectionObserver" in window) {
        new IntersectionObserver(([entry]) => { visible=entry.isIntersecting; sync(); },{rootMargin:"40px"}).observe(scene);
      } else {
        visible=true;
        sync();
      }
      new ResizeObserver(measure).observe(projects);
      projects.addEventListener("scroll", schedule, {passive:true});
      motion.addEventListener("change", sync);
      toggle?.addEventListener("click", sync);
      document.addEventListener("visibilitychange", sync);
      tags.forEach((tag,index) => tag.addEventListener("click", event => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        projects.scrollTo({left:stops[index],behavior:railMotion()?"smooth":"instant"});
      }));

      projects.addEventListener("click", event => {
        const link = event.target.closest("a[href]");
        if (!link || event.defaultPrevented || event.detail===0 || event.button!==0 || !railMotion() ||
            event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
            link.hasAttribute("download") || (link.target && link.target!=="_self") || !Element.prototype.animate) return;
        const url = new URL(link.href);
        if (url.origin!==location.origin || url.pathname===location.pathname) return;
        event.preventDefault();
        if (flash) return;
        flash=document.createElement("div");
        flash.className="tl-arc-flash";
        flash.setAttribute("aria-hidden","true");
        document.body.append(flash);
        flash.animate([
          {transform:"translate3d(-65vw,0,0) skewX(-18deg)",opacity:0},
          {opacity:.60,offset:.54},
          {transform:"translate3d(114vw,0,0) skewX(-18deg)",opacity:0}
        ],{duration:180,easing:"cubic-bezier(.25,.65,.36,1)"}).finished.then(() => location.assign(url.href), () => {
          flash?.remove();flash=undefined;
        });
      });
      addEventListener("pageshow", () => { flash?.remove();flash=undefined; });
      measure();
    }
  }

  const picker = document.querySelector("#tl-podbor > .tl-home-picker");
  if (picker) {
    const openFromLink = () => { if (location.hash==="#tl-podbor") picker.open=true; };
    addEventListener("hashchange",openFromLink);
    document.addEventListener("click",event => {
      if (event.target.closest('a[href="#tl-podbor"]')) picker.open=true;
    });
    openFromLink();
  }

  const shelf = document.querySelector(".tl-book-shelf");
  const shelfControls = document.querySelector(".tl-orbit-tools");
  if (shelf && shelfControls && window.TL) {
    const books = [...shelf.querySelectorAll(".tl-book-volume")];
    const buttons = [...shelfControls.querySelectorAll("button[data-orbit]")];
    const link = shelfControls.querySelector("a");
    const label = link.querySelector("span");

    if (books.length === 3) {
      let turn = 1, target = 1, startTurn = 1, startTime;
      let distance = 0;
      let gesture;
      function measure() {
        const gap = parseFloat(getComputedStyle(shelf).columnGap) || 0;
        distance = books[0].offsetWidth + gap;
        draw();
      }
      function draw() {
        books.forEach((book,index) => {
          const angle = (index-turn)*Math.PI*2/3;
          const depth = Math.cos(angle);
          const side = Math.sin(angle);
          const x = side * distance / .866;
          const y = (1-depth) * 6;
          const z = (depth-1) * (distance > 140 ? 48 : 26);
          const size = .94 + depth*.055;
          book.style.transform = `translate3d(${x}px,${y}px,${z}px) rotateY(${side*-22}deg) rotateZ(${side*4}deg) scale(${size})`;
          book.style.zIndex = String(Math.round(depth*10)+12);
        });
      }
      function tick(now) {
        if (startTime === undefined) startTime = now;
        const progress = Math.min(1,(now-startTime)/590);
        const easing = (1-Math.cos(Math.PI*progress))/2;
        turn = startTurn + (target-startTurn)*easing;
        draw();
        if (progress===1) TL.tick.remove(tick);
      }
      function rotate(direction) {
        const index = ((target + direction) % books.length + books.length) % books.length;
        target += direction;
        link.href = books[index].dataset.href;
        label.textContent = books[index].dataset.title;
        if (motion.matches) {
          turn = target;
          TL.tick.remove(tick);
          draw();
          return;
        }
        startTurn = turn;
        startTime = undefined;
        TL.tick.add(tick);
      }
      shelf.classList.add("tl-orbit-ready");
      buttons.forEach(button => {
        button.hidden = false;
        button.addEventListener("click",() => rotate(Number(button.dataset.orbit)));
      });
      const vitrine = shelf.closest(".tl-book-vitrine");
      vitrine.addEventListener("keydown", event => {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        rotate(event.key === "ArrowRight" ? 1 : -1);
      });
      shelf.addEventListener("pointerdown", event => {
        if (!event.isPrimary || (event.pointerType === "mouse" && event.button !== 0)) return;
        gesture = {id:event.pointerId, x:event.clientX, y:event.clientY};
        shelf.setPointerCapture(event.pointerId);
      });
      shelf.addEventListener("pointerup", event => {
        if (!gesture || gesture.id !== event.pointerId) return;
        const dx = event.clientX - gesture.x, dy = event.clientY - gesture.y;
        if (Math.abs(dx)>38 && Math.abs(dx)>Math.abs(dy)*1.35) rotate(dx<0 ? 1 : -1);
        gesture = null;
      });
      shelf.addEventListener("pointercancel",() => { gesture = null; });
      shelf.addEventListener("dragstart", event => event.preventDefault());
      motion.addEventListener("change",() => {
        if (motion.matches) { TL.tick.remove(tick); turn=target; draw(); }
      });
      new ResizeObserver(measure).observe(shelf);
      measure();
    }
  }

  const basket = document.querySelector(".sh-cart-btn");
  let basketSlot;
  let docked = false;
  function dockBasket() {
    if (!basketSlot) return;
    const offscreen = basketSlot.getBoundingClientRect().bottom <= 0;
    if (offscreen === docked) return;
    docked = offscreen;
    const focused = document.activeElement === basket;
    basket.classList.toggle("tl-cart-docked", docked);
    if (docked) document.body.append(basket);
    else basketSlot.append(basket);
    if (focused) basket.focus({preventScroll:true});
  }
  if (basket) {
    basketSlot = document.createElement("span");
    basketSlot.className = "tl-cart-slot";
    basket.before(basketSlot);
    basketSlot.append(basket);
    new IntersectionObserver(dockBasket).observe(basketSlot);
  }

  let flight = null;
  function flyBook(button) {
    const cover = button.closest(".sh-card:not(.is-svc)")?.querySelector(".sh-ph img");
    dockBasket();
    if (!cover?.complete || !cover.naturalWidth || !basket || document.hidden || !button.animate) return false;
    const to = basket.getBoundingClientRect();
    if (!to.width || to.bottom < 0 || to.top > innerHeight) return false;

    flight?.cancel();
    const photo = cover.getBoundingClientRect();
    const trigger = button.getBoundingClientRect();
    const visible = photo.bottom>20 && photo.top<innerHeight-30 && photo.right>0 && photo.left<innerWidth;
    const from = visible ? photo : trigger;
    const w = innerWidth<768 ? 32 : 49;
    const h = w*1.5;
    const left = Math.max(0,Math.min(innerWidth-w,from.left+(from.width-w)/2));
    const top = Math.max(0,Math.min(innerHeight-h,from.top+(from.height-h)/2));
    const destX = to.left+(to.width-w)/2;
    const destY = to.top+(to.height-h)/2;
    const ghost = document.createElement("div");
    ghost.className = "tl-cart-flight";
    ghost.setAttribute("aria-hidden","true");
    ghost.style.setProperty("--tl-flight-width",`${w}px`);
    ghost.style.setProperty("--tl-flight-height",`${h}px`);
    const image = new Image();
    image.alt = "";
    image.src = cover.currentSrc || cover.src;
    ghost.append(image);
    document.body.append(ghost);
    const lift = Math.min(98, Math.max(23, Math.abs(top-destY)*.20));
    const effect = ghost.animate([
      {transform:`translate3d(${left}px,${top}px,0) rotate(-9deg) scale(1.04)`,opacity:.96},
      {transform:`translate3d(${left+(destX-left)*.53}px,${Math.max(0,(top+destY)/2-lift)}px,0) rotate(13deg) scale(.88)`,opacity:1,offset:.52},
      {transform:`translate3d(${destX}px,${destY}px,0) rotate(3deg) scale(.22)`,opacity:.1}
    ],{duration:520,easing:"cubic-bezier(.38,.12,.28,1)"});
    flight = effect;
    const clean = () => { ghost.remove(); if (flight===effect) flight=null; };
    effect.oncancel = clean;
    effect.onfinish = () => {
      clean();
      if (basket.isConnected && !motion.matches)
        basket.animate([{transform:"scale(1)"},{transform:"scale(1.13)"},{transform:"scale(1)"}],
          {duration:225,easing:"cubic-bezier(.23,1,.32,1)"});
    };
    return true;
  }
  motion.addEventListener("change",() => { if (motion.matches) flight?.cancel(); });
  addEventListener("pagehide",() => flight?.cancel());

  if (document.body.classList.contains("shop")) {
    document.addEventListener("tl-cart-added",event => {
      if (motion.matches) return;
      if (flyBook(event.target)) return;
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
