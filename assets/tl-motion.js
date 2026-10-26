/* TimLabs — слой движения (25.10.2026; контракт движения 26.10.2026). Школа Эмиля Ковальски: transform/opacity, сильные кривые,
   одна мотивация на эффект. Контракт по смыслу из textura-agency/ai-design-vault (Unlicense), код наш:
   TL.tick (один общий цикл кадра) · TL.spring (одна пружина) · TL.Inview · TL.SpringTrigger · TL.Hover · TL.Handle.
   Ни одного @keyframes и второй библиотеки. prefers-reduced-motion — сразу конечное состояние; содержимое всегда в DOM.
   Живое поле — фирменный знак «живой мозг × web 4.0»; нить света, приезд из расфокуса и стеклянное окно — приёмы слоя Relay. */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement, W = window;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
  root.classList.add("js");
  var TL = W.TL = W.TL || {};
  TL.reduce = reduce; TL.fine = fine;
  /* приёмы Relay включаются стилем: --tl-relay: "thread focus window" в tl-paper.css (убрать слово — приём погашен) */
  var relay = (getComputedStyle(root).getPropertyValue("--tl-relay") || "");
  TL.relay = function (k) { return relay.indexOf(k) >= 0; };
  function $$(s, el) { return typeof s === "string" ? (el || doc).querySelectorAll(s) : (s && s.length !== undefined ? s : (s ? [s] : [])); }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  /* старые якоря и раскрытие «Проводы» */
  var go = { zamysel: "/beremennost-i-rody/", rozhdenie: "/beremennost-i-rody/", telo: "/telo-i-vosstanovlenie/", dukh: "/retrity-i-kmv/", detstvo: "/journal/" };
  var hh = location.hash.slice(1);
  if (go[hh]) { location.replace(go[hh]); return; }
  if (hh === "provody") { var pv = doc.querySelector("#provody details"); if (pv) pv.open = true; }

  /* ── общий цикл кадра: один requestAnimationFrame на всю страницу, спит без подписчиков и на скрытой вкладке ── */
  var subs = [], rafId = 0;
  function frame(t) {
    rafId = 0;
    var list = subs.slice();
    for (var i = 0; i < list.length; i++) { try { list[i](t); } catch (e) { TL.tick.remove(list[i]); } }
    wake();
  }
  function wake() { if (!rafId && subs.length && !doc.hidden) rafId = requestAnimationFrame(frame); }
  TL.tick = {
    add: function (fn) { if (subs.indexOf(fn) < 0) subs.push(fn); wake(); return fn; },
    remove: function (fn) { var i = subs.indexOf(fn); if (i >= 0) subs.splice(i, 1); }
  };
  doc.addEventListener("visibilitychange", wake);

  /* ── одна пружина: жёсткость 170, затухание 26, масса 1 (почти критическое — без перелёта) ── */
  TL.spring = function (o) {
    o = o || {};
    var x = o.from || 0, v = 0, to = x, k = o.k || 170, c = o.c || 26, m = o.m || 1, last = 0, run = false, eps = o.eps || 0.001;
    function out() { if (o.onUpdate) o.onUpdate(x); }
    function step(t) {
      var dt = last ? Math.min(0.064, (t - last) / 1000) : 1 / 60; last = t;
      var n = Math.ceil(dt * 240), h = dt / n;
      for (var i = 0; i < n; i++) { var a = (-k * (x - to) - c * v) / m; v += a * h; x += v * h; }
      if (Math.abs(x - to) < eps && Math.abs(v) < eps) { x = to; v = 0; stop(); out(); if (o.onDone) o.onDone(x); return; }
      out();
    }
    function stop() { run = false; last = 0; TL.tick.remove(step); }
    var api = {
      set: function (target) {
        to = target;
        if (reduce) { x = to; v = 0; out(); return api; }
        if (!run) { run = true; TL.tick.add(step); }
        return api;
      },
      jump: function (val) { x = to = val; v = 0; stop(); out(); return api; },
      value: function () { return x; },
      stop: stop
    };
    return api;
  };

  /* ── Inview: появление при входе в экран (класс; переход делает CSS), один раз или каждый раз ── */
  TL.Inview = function (sel, opt) {
    opt = opt || {};
    var cls = opt.cls || "in", els = $$(sel);
    function enter(el) { el.classList.add(cls); if (opt.onEnter) opt.onEnter(el); }
    if (reduce || !("IntersectionObserver" in W)) { for (var i = 0; i < els.length; i++) enter(els[i]); return null; }
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) { if (opt.mode === "repeat") e.target.classList.remove(cls); return; }
        enter(e.target);
        if (opt.mode !== "repeat") io.unobserve(e.target);
      });
    }, { rootMargin: opt.margin || "0px 0px -8% 0px" });
    for (var j = 0; j < els.length; j++) io.observe(els[j]);
    return io;
  };

  /* ── SpringTrigger: движение от прокрутки. Грамматика позиции: "<точка элемента> <точка окна>",
     точки — top | center | bottom | N% | Npx (например "top 80%": верх элемента дошёл до 80 % высоты окна).
     mode "scrub" — onProgress(0…1) через пружину; mode "toggle" — класс/onToggle при пересечении start ── */
  function edge(tok, size) {
    if (!tok || tok === "top") return 0;
    if (tok === "center") return size / 2;
    if (tok === "bottom") return size;
    if (/%$/.test(tok)) return size * parseFloat(tok) / 100;
    return parseFloat(tok) || 0;
  }
  TL.SpringTrigger = function (el, opt) {
    opt = opt || {};
    var mode = opt.mode || "scrub", start = (opt.start || "top bottom").split(/\s+/), end = (opt.end || "bottom top").split(/\s+/);
    var sY = 0, eY = 1, on = null, sp = null;
    function measure() {
      var r = el.getBoundingClientRect(), y = r.top + scrollY, h = r.height, vh = innerHeight;
      sY = y + edge(start[0], h) - edge(start[1], vh);
      eY = y + edge(end[0], h) - edge(end[1], vh);
      if (eY <= sY) eY = sY + 1;
    }
    function progress() { return clamp((scrollY - sY) / (eY - sY), 0, 1); }
    function update() {
      if (mode === "scrub") { if (opt.smooth === false || reduce) opt.onProgress(progress()); else sp.set(progress()); return; }
      var s = scrollY >= sY;
      if (s !== on) { on = s; if (opt.cls) el.classList.toggle(opt.cls, s); if (opt.onToggle) opt.onToggle(s); }
    }
    if (mode === "scrub") sp = TL.spring({ onUpdate: opt.onProgress, eps: 0.0005 });
    measure();
    if (sp) sp.jump(progress()); else update();
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", function () { measure(); update(); }, { passive: true });
    if ("ResizeObserver" in W) new ResizeObserver(function () { measure(); update(); }).observe(doc.body);
    return { measure: measure, update: update, progress: progress };
  };

  /* ── Hover: наведение мышью, на касании выключено. tilt — наклон до N°, shift — сдвиг до N px; пружина возвращает в 0 ── */
  TL.Hover = function (sel, opt) {
    opt = opt || {};
    var els = $$(sel), out = [];
    if (!fine || reduce) return out;
    for (var i = 0; i < els.length; i++) (function (el) {
      var X = 0, Y = 0;
      function apply() {
        X = sx.value(); Y = sy.value();
        if (opt.tilt) el.style.transform = (X || Y) ? "perspective(1200px) rotateX(" + (-Y * opt.tilt).toFixed(2) + "deg) rotateY(" + (X * opt.tilt).toFixed(2) + "deg)" : "";
        else if (opt.shift) el.style.transform = (X || Y) ? "translate(" + (X * opt.shift).toFixed(1) + "px," + (Y * opt.shift).toFixed(1) + "px)" : "";
        if (opt.onMove) opt.onMove(X, Y, el);
      }
      var sx = TL.spring({ onUpdate: apply }), sy = TL.spring({ onUpdate: apply });
      el.addEventListener("pointermove", function (e) {
        if (e.pointerType !== "mouse") return;
        var r = el.getBoundingClientRect();
        sx.set(clamp((e.clientX - r.left) / r.width * 2 - 1, -1, 1)); sy.set(clamp((e.clientY - r.top) / r.height * 2 - 1, -1, 1));
      });
      el.addEventListener("pointerleave", function () { sx.set(0); sy.set(0); });
      out.push(el);
    })(els[i]);
    return out;
  };

  /* ── Handle: перетаскивание по оси с пружинным доводом к ближайшей точке snap; стрелки клавиатуры — шаг ── */
  TL.Handle = function (el, opt) {
    opt = opt || {};
    var axis = opt.axis === "y" ? "y" : "x", min = opt.min || 0, max = opt.max === undefined ? 100 : opt.max, val = opt.value || min, from = 0, p0 = 0, drag = false;
    function apply(v) { val = v; el.style.transform = axis === "x" ? "translateX(" + v.toFixed(1) + "px)" : "translateY(" + v.toFixed(1) + "px)"; if (opt.onMove) opt.onMove(v); }
    var sp = TL.spring({ from: val, onUpdate: apply, onDone: function (v) { if (opt.onRelease) opt.onRelease(v); } });
    function near(v) {
      var s = opt.snap; if (!s) return v;
      if (typeof s === "number") return clamp(Math.round((v - min) / s) * s + min, min, max);
      var best = s[0]; for (var i = 1; i < s.length; i++) if (Math.abs(s[i] - v) < Math.abs(best - v)) best = s[i]; return best;
    }
    el.style.touchAction = axis === "x" ? "pan-y" : "pan-x";
    el.addEventListener("pointerdown", function (e) { drag = true; from = val; p0 = axis === "x" ? e.clientX : e.clientY; el.setPointerCapture(e.pointerId); sp.jump(val); });
    el.addEventListener("pointermove", function (e) { if (!drag) return; sp.jump(clamp(from + (axis === "x" ? e.clientX : e.clientY) - p0, min, max)); });
    function up() { if (!drag) return; drag = false; sp.set(near(val)); }
    el.addEventListener("pointerup", up); el.addEventListener("pointercancel", up);
    el.addEventListener("keydown", function (e) {
      var st = typeof opt.snap === "number" ? opt.snap : (max - min) / 10, d = { ArrowRight: st, ArrowDown: st, ArrowLeft: -st, ArrowUp: -st }[e.key];
      if (d) { e.preventDefault(); sp.set(near(clamp(sp.value() + d, min, max))); }
    });
    apply(val);
    return { set: function (v) { sp.set(near(clamp(v, min, max))); }, value: function () { return val; } };
  };

  /* ════ применение на сайте ════ */

  /* появление: группы со ступенькой 70 мс, не больше 6; карточки и шапки разделов — из расфокуса (Relay) */
  doc.querySelectorAll(".pp-bento,.pp-index,.tlg-grid,.pp-facts,.pj-grid").forEach(function (g) {
    var kids = g.querySelectorAll(":scope > .rv, :scope > div");
    for (var k = 0; k < kids.length && k < 6; k++) { kids[k].style.transitionDelay = (k * 70) + "ms"; kids[k].style.setProperty("--rv-d", (k * 70) + "ms"); }
  });
  if (!reduce && TL.relay("focus")) doc.querySelectorAll(".pp-head.rv,.tlg-head.rv,.pp-tile.rv,.pj-card.rv,.pj-feature.rv,.gcard.rv,.pp-row.rv").forEach(function (el) {
    el.classList.add("rv-focus");
    function done(e) { if (e && e.propertyName && e.propertyName !== "opacity") return; el.classList.remove("rv-focus"); el.style.removeProperty("--rv-d"); el.removeEventListener("transitionend", done); }
    el.addEventListener("transitionend", done);
  });
  TL.Inview(".rv", {
    onEnter: function (el) {
      el.querySelectorAll("[data-count]").forEach(count);
      if (el.hasAttribute("data-count")) count(el);
    }
  });

  /* счётчик чисел (700 мс, 1 − (1 − p)³) через общий цикл */
  function count(el) {
    if (el.__tl) return; el.__tl = 1;
    var to = parseInt(el.getAttribute("data-count") || el.textContent, 10);
    if (!to || reduce) return;
    var t0 = 0, d = 700;
    TL.tick.add(function tick(t) {
      if (!t0) t0 = t;
      var p = Math.min(1, (t - t0) / d); p = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(to * p);
      if (p >= 1) TL.tick.remove(tick);
    });
  }

  /* шапка при прокрутке > 24 px */
  var top = doc.querySelector(".pp-top");
  if (top) TL.SpringTrigger(doc.body, { mode: "toggle", start: "top -24px", onToggle: function (s) { top.classList.toggle("is-scrolled", s); } });

  /* магнитная главная кнопка: до 3 px от центра к курсору, только мышь */
  TL.Hover(".pp-btn:not(.line):not(.ink)", { shift: 3 });

  /* стеклянное окно первого экрана: наклон ≤ 4° за курсором, блик сдвигается следом (Relay); на телефоне — статика */
  if (TL.relay("window")) TL.Hover(".pp-hero-photo", {
    tilt: 4, onMove: function (x, y, el) {
      el.style.setProperty("--gx", (x * 12).toFixed(1) + "%"); el.style.setProperty("--gy", (y * 12).toFixed(1) + "%");
      el.style.setProperty("--go", Math.min(1, Math.abs(x) + Math.abs(y)).toFixed(2));
    }
  });

  /* нить света через страницу (Relay): один SVG-путь по левому полю через опорные точки, дорисовывается при прокрутке */
  (function thread() {
    var main = doc.querySelector("main"); if (!main || !TL.relay("thread")) return;
    var anchors = $$("[data-thread]", main);
    if (anchors.length < 2) anchors = [].slice.call(doc.querySelectorAll(".pp-hero .pp-cta .pp-btn, #put .pp-head h2, #mastera .pp-head h2, #svyaz h2"));
    if (anchors.length < 2) return;
    var NS = "http://www.w3.org/2000/svg", svg = doc.createElementNS(NS, "svg"), path = doc.createElementNS(NS, "path"), defs = doc.createElementNS(NS, "defs"),
      grad = doc.createElementNS(NS, "linearGradient"), nodes = [], L = 1, marks = [], p = 0, built = false;
    svg.setAttribute("class", "tl-thread"); svg.setAttribute("aria-hidden", "true"); svg.setAttribute("focusable", "false");
    grad.setAttribute("id", "tl-thread-g"); grad.setAttribute("x1", "0"); grad.setAttribute("x2", "0"); grad.setAttribute("y1", "0"); grad.setAttribute("y2", "1");
    [[0, 0], [0.04, 1], [0.96, 1], [1, 0]].forEach(function (s) { var st = doc.createElementNS(NS, "stop"); st.setAttribute("offset", s[0]); st.setAttribute("stop-opacity", s[1]); st.setAttribute("class", "tl-thread-stop"); grad.appendChild(st); });
    defs.appendChild(grad); svg.appendChild(defs); path.setAttribute("class", "tl-thread-path"); svg.appendChild(path); main.appendChild(svg);
    function draw(v) {
      p = v; path.style.strokeDashoffset = (L * (1 - p)).toFixed(1);
      for (var i = 0; i < nodes.length; i++) nodes[i].classList.toggle("on", p >= marks[i] - 0.002);
    }
    function build() {
      if (getComputedStyle(svg).display === "none") { built = false; return; }
      var mr = main.getBoundingClientRect(), wrap = anchors[0].closest(".pp-wrap") || main, cl = wrap.getBoundingClientRect().left + parseFloat(getComputedStyle(wrap).paddingLeft) - mr.left;
      var xn = Math.max(12, cl - 16), xb = Math.max(6, xn - Math.min(56, xn - 6) * 0.6), pts = [];
      anchors.forEach(function (a) { var r = a.getBoundingClientRect(); pts.push(r.top - mr.top + Math.min(r.height / 2, 28)); });
      var y0 = pts[0] - 8, h = pts[pts.length - 1] - y0 + 8, d = "M" + xn + " " + (pts[0] - y0).toFixed(1);
      for (var i = 1; i < pts.length; i++) {
        var a = pts[i - 1] - y0, b = pts[i] - y0, g = (b - a) * 0.38;
        d += " C" + xb.toFixed(1) + " " + (a + g).toFixed(1) + " " + xb.toFixed(1) + " " + (b - g).toFixed(1) + " " + xn + " " + b.toFixed(1);
      }
      svg.style.top = y0.toFixed(1) + "px"; svg.style.height = h.toFixed(1) + "px"; svg.style.width = (xn + 8) + "px";
      svg.setAttribute("viewBox", "0 0 " + (xn + 8) + " " + h.toFixed(1)); grad.setAttribute("gradientUnits", "userSpaceOnUse"); grad.setAttribute("y2", h.toFixed(1));
      path.setAttribute("d", d); L = path.getTotalLength() || 1; path.style.strokeDasharray = L.toFixed(1);
      nodes.forEach(function (n) { n.remove(); }); nodes = []; marks = [];
      var probe = doc.createElementNS(NS, "path");
      pts.forEach(function (y, i) {
        var c = doc.createElementNS(NS, "circle"); c.setAttribute("cx", xn); c.setAttribute("cy", (y - y0).toFixed(1)); c.setAttribute("r", "3"); c.setAttribute("class", "tl-thread-node");
        svg.appendChild(c); nodes.push(c);
        if (!i) { marks.push(0); return; }
        probe.setAttribute("d", d.split(" C").slice(0, i + 1).join(" C")); marks.push(probe.getTotalLength() / L);
      });
      built = true; draw(p);
    }
    build();
    if (reduce) { draw(1); addEventListener("resize", function () { build(); draw(1); }, { passive: true }); return; }
    var trig = TL.SpringTrigger(svg, { mode: "scrub", start: "top 75%", end: "bottom 60%", onProgress: function (v) { if (built) draw(v); } });
    var again = 0;
    function rebuild() { if (again) return; again = 1; TL.tick.add(function once() { TL.tick.remove(once); again = 0; build(); trig.measure(); trig.update(); }); }
    addEventListener("resize", rebuild, { passive: true });
    if ("ResizeObserver" in W) new ResizeObserver(rebuild).observe(main);
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(rebuild);
  })();

  /* тема: день / ночь (кнопка в шапке, память в localStorage); «авто» по устройству */
  function isLight() { return root.getAttribute("data-theme") === "light" || (root.getAttribute("data-theme") !== "dark" && root.classList.contains("auto-light")); }
  doc.querySelectorAll(".pp-theme").forEach(function (b) {
    b.addEventListener("click", function () {
      var light = !isLight();
      root.classList.remove("auto-light"); root.setAttribute("data-theme", light ? "light" : "dark");
      try { localStorage.setItem("tl-theme", light ? "light" : "dark"); } catch (e) {}
      try { if (typeof ym === "function") ym(111725024, "reachGoal", "theme_switch", { to: light ? "light" : "dark" }); } catch (e) {}
    });
  });

  /* меню на телефоне закрывается по выбору */
  doc.querySelectorAll(".pp-menu a").forEach(function (a) { a.addEventListener("click", function () { a.closest("details").open = false; }); });

  /* живое поле: 4 пятна, 30 кадров/с, половинное разрешение; живёт в общем цикле, спит вне экрана, на скрытой вкладке и во время прокрутки */
  var c = doc.getElementById("tl-field");
  if (!c || reduce || !c.getContext) return;
  var ctx = c.getContext("2d", { alpha: true }), Wd, H, dpr, blobs = [], mx = .7, my = .3, tx = .7, ty = .3, last = 0, visible = true, scrolled = -1e9;
  addEventListener("scroll", function () { scrolled = performance.now(); }, { passive: true });
  var COLORS = [[79, 180, 242], [124, 124, 255], [79, 180, 242], [168, 107, 255]];
  function size() {
    dpr = Math.min(1, devicePixelRatio || 1) * .5;
    var cw = c.clientWidth || root.clientWidth, ch = c.clientHeight || Math.min(innerHeight, 1200);
    Wd = c.width = Math.ceil(cw * dpr); H = c.height = Math.ceil(ch * dpr);
  }
  function seed() {
    blobs = COLORS.map(function (col, i) {
      return { col: col, x: .2 + .6 * Math.random(), y: .2 + .6 * Math.random(), r: .28 + .12 * Math.random(), ph: i * 1.7, sp: .12 + .05 * i, pull: .05 + .04 * i };
    });
  }
  function draw(t) {
    if (t - last < 33 || t - scrolled < 200) return;     /* во время прокрутки поле не перерисовывается: кадр прокрутки ≤ 50 мс */
    last = t;
    mx += (tx - mx) * .04; my += (ty - my) * .04;
    ctx.clearRect(0, 0, Wd, H);
    var light = isLight();
    ctx.globalCompositeOperation = light ? "multiply" : "lighter";
    var s = t / 1000, a0 = light ? .22 : .16, a1 = light ? .07 : .05;
    for (var i = 0; i < blobs.length; i++) {
      var b = blobs[i];
      var bx = b.x + Math.sin(s * b.sp + b.ph) * .08 + (mx - b.x) * b.pull;
      var by = b.y + Math.cos(s * b.sp * .8 + b.ph) * .07 + (my - b.y) * b.pull;
      var br = b.r * (1 + Math.sin(s * .35 + b.ph) * .08) * Math.max(Wd, H);
      var g = ctx.createRadialGradient(bx * Wd, by * H, 0, bx * Wd, by * H, br);
      g.addColorStop(0, "rgba(" + b.col.join(",") + "," + a0 + ")"); g.addColorStop(.55, "rgba(" + b.col.join(",") + "," + a1 + ")"); g.addColorStop(1, "rgba(" + b.col.join(",") + ",0)");
      ctx.fillStyle = g; ctx.fillRect(0, 0, Wd, H);
    }
  }
  function run() { if (visible && !doc.hidden) TL.tick.add(draw); else TL.tick.remove(draw); }
  size(); seed(); run();
  addEventListener("resize", size, { passive: true });
  addEventListener("pointermove", function (e) { tx = e.clientX / (c.clientWidth || 1); ty = e.clientY / (c.clientHeight || 1); }, { passive: true });
  doc.addEventListener("visibilitychange", run);
  new IntersectionObserver(function (es) { visible = es[0].isIntersecting; run(); }).observe(c);
})();
