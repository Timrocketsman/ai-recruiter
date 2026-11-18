/* Native horizontal scrolling, circular perspective and explicit controls. */
(() => {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const rails = [];
  const isPaused = () => {
    if (reduced.matches) return true;
    try { return localStorage.getItem("tl-studio-motion") === "paused"; }
    catch { return false; }
  };

  let paused = isPaused();

  function enhance(rail) {
    const track = rail.querySelector(".tl-rail-scroll");
    const tools = rail.querySelector(".tl-rail-tools");
    const slots = [...track.children];
    if (slots.length < 2 || rail.hasAttribute('data-enhanced')) return;
    const cards = slots.map(slot => slot.firstElementChild);
    const books = rail.dataset.rail === "books";
    const prev = makeButton("←", "Предыдущая карточка");
    const next = makeButton("→", "Следующая карточка");
    const number = document.createElement("span");
    number.className = "tl-rail-index";
    number.setAttribute("aria-live", "polite");
    number.setAttribute("aria-atomic", "true");
    const meter = document.createElement("span");
    meter.className = "tl-rail-meter";
    meter.setAttribute("aria-hidden", "true");
    tools.append(prev, number, next, meter);
    rail.dataset.enhanced = "";
    let stops = [];
    let width = 1;
    let active = -1;
    let frame = 0;
    let announce;
    let gesture;
    let suppressClick = false;

    function makeButton(symbol, label) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = symbol;
      button.setAttribute("aria-label", label);
      button.setAttribute("aria-controls", track.id);
      return button;
    }

    function measure() {
      if (!track.clientWidth) return;
      const start = slots[0].offsetLeft;
      const end = track.scrollWidth - track.clientWidth;
      width = slots[0].offsetWidth + (parseFloat(getComputedStyle(track).columnGap) || 0);
      stops = slots.map(slot => Math.min(end, slot.offsetLeft - start));
      render();
    }

    function render() {
      if (!stops.length) return;
      const scroll = track.scrollLeft;
      const current = stops.reduce((best, stop, index) =>
        Math.abs(stop - scroll) < Math.abs(stops[best] - scroll) ? index : best, 0);
      slots.forEach((slot, index) => {
        const distance = (stops[index] - scroll) / width;
        if (paused) {
          cards[index].style.removeProperty("--rail-transform");
        } else {
          const angle = Math.atan(distance * (books ? .88 : .66));
          const curve = 1 - Math.cos(angle);
          const x = -distance * width * Math.min(curve * .36, .19);
          const y = curve * (books ? 52 : 34);
          const z = -curve * (books ? 240 : 192);
          cards[index].style.setProperty("--rail-transform",
            `perspective(840px) translate3d(${x.toFixed(1)}px,${y.toFixed(1)}px,${z.toFixed(1)}px) rotateY(${angle.toFixed(4)}rad)`);
        }
        if (current !== active) {
          if (index === current) slot.setAttribute("aria-current", "true");
          else slot.removeAttribute("aria-current");
        }
      });
      meter.style.setProperty("--rail-progress", Math.min(1, (scroll / width + 1) / slots.length));
      if (current === active) return;
      active = current;
      prev.setAttribute("aria-disabled", String(active === 0));
      next.setAttribute("aria-disabled", String(active === slots.length - 1));
      clearTimeout(announce);
      announce = setTimeout(() => { number.textContent = `${active + 1} / ${slots.length}`; }, 160);
    }

    function schedule() {
      if (frame) return;
      frame = requestAnimationFrame(() => { frame = 0; render(); });
    }

    function go(index, instant = false) {
      if (!stops.length) return;
      index = Math.max(0, Math.min(index, slots.length - 1));
      track.scrollTo({left: stops[index], behavior: instant || paused ? "instant" : "smooth"});
    }

    function step(direction) {
      const now = track.scrollLeft;
      const target = direction > 0 ? stops.findIndex(stop => stop > now + 3)
        : stops.findLastIndex(stop => stop < now - 3);
      if (target >= 0) go(target);
    }

    prev.addEventListener("click", () => step(-1));
    next.addEventListener("click", () => step(1));
    track.addEventListener("scroll", schedule, {passive: true});
    track.addEventListener("keydown", event => {
      if (event.target !== track || event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
        event.preventDefault();
        step(event.key === "ArrowRight" ? 1 : -1);
      } else if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        go(event.key === "Home" ? 0 : slots.length - 1);
      }
    });
    track.addEventListener("focusin", event => {
      const slot = event.target.closest(".tl-rail-slot");
      // Ensure links reached with Tab settle front-on. Mouse clicks keep their target.
      if (slot && event.target.matches(":focus-visible")) go(slots.indexOf(slot), true);
    });

    track.addEventListener("pointerdown", event => {
      if (event.pointerType !== "mouse" || event.button !== 0) return;
      suppressClick = false;
      gesture = {id: event.pointerId, x: event.clientX, origin: track.scrollLeft};
    });
    track.addEventListener("pointermove", event => {
      if (!gesture || event.pointerId !== gesture.id || !(event.buttons & 1)) return;
      const shift = event.clientX - gesture.x;
      if (!suppressClick && Math.abs(shift) < 8) return;
      if (!suppressClick) {
        track.setPointerCapture(event.pointerId);
        track.classList.add("is-dragging");
        suppressClick = true;
      }
      track.scrollLeft = gesture.origin - shift;
    });
    const endDrag = () => {
      if (!gesture) return;
      gesture = undefined;
      if (!suppressClick) return;
      render();
      track.classList.remove("is-dragging");
      go(active);
    };
    track.addEventListener("pointerup", endDrag);
    track.addEventListener("pointercancel", endDrag);
    track.addEventListener("lostpointercapture", endDrag);
    track.addEventListener("dragstart", event => event.preventDefault());
    track.addEventListener("click", event => {
      if (!suppressClick || event.detail === 0) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressClick = false;
    }, true);

    new ResizeObserver(measure).observe(track);
    rails.push(schedule);
    measure();
  }

  const near = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      near.unobserve(entry.target);
      enhance(entry.target);
    }
  }, {rootMargin: "260px 0px"});
  for (const rail of document.querySelectorAll("[data-rail]")) {
    near.observe(rail);
    rail.addEventListener("focusin", () => {
      near.unobserve(rail);
      enhance(rail);
    }, {once: true});
  }

  const refresh = () => {
    paused = isPaused();
    rails.forEach(schedule => schedule());
  };
  reduced.addEventListener("change", refresh);
  window.addEventListener("storage", event => {
    if (event.key === "tl-studio-motion") refresh();
  });
  document.addEventListener("click", event => {
    if (event.target.closest(".tl-motion-toggle,.tl-space-control")) refresh();
  });
})();
