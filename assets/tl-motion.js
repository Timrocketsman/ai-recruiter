/* TimLabs — слой движения (25.10.2026). Школа Эмиля Ковальски: только transform/opacity, сильные кривые, одна мотивация на эффект.
   Живое поле — фирменный знак «живой мозг × web 4.0»: 4 мягких пятна дышат и тянутся к курсору; ≤2 % процессора, пауза вне вкладки.
   Всё выключается при prefers-reduced-motion. Без зависимостей. */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
  root.classList.add("js");

  /* старые якоря и раскрытие «Проводы» */
  var go = { zamysel: "/beremennost-i-rody/", rozhdenie: "/beremennost-i-rody/", telo: "/telo-i-vosstanovlenie/", dukh: "/retrity-i-kmv/", detstvo: "/journal/" };
  var hh = location.hash.slice(1);
  if (go[hh]) { location.replace(go[hh]); return; }
  if (hh === "provody") { var pv = doc.querySelector("#provody details"); if (pv) pv.open = true; }

  /* появление при прокрутке: группы со ступенькой 70 мс, не больше 6 */
  var els = doc.querySelectorAll(".rv");
  if (reduce || !("IntersectionObserver" in window)) {
    for (var i = 0; i < els.length; i++) els[i].classList.add("in");
  } else {
    doc.querySelectorAll(".pp-bento,.pp-index,.tlg-grid,.pp-facts").forEach(function (g) {
      var kids = g.querySelectorAll(":scope > .rv, :scope > div");
      for (var k = 0; k < kids.length && k < 6; k++) kids[k].style.transitionDelay = (k * 70) + "ms";
    });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add("in"); io.unobserve(e.target);
        e.target.querySelectorAll("[data-count]").forEach(count);
        if (e.target.hasAttribute("data-count")) count(e.target);
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    for (var j = 0; j < els.length; j++) io.observe(els[j]);
  }

  /* счётчик чисел */
  function count(el) {
    if (el.__tl) return; el.__tl = 1;
    var to = parseInt(el.getAttribute("data-count") || el.textContent, 10);
    if (!to || reduce) return;
    var t0 = performance.now(), d = 700;
    (function tick(t) {
      var p = Math.min(1, (t - t0) / d); p = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(to * p);
      if (p < 1) requestAnimationFrame(tick);
    })(t0);
  }

  /* шапка при прокрутке */
  var top = doc.querySelector(".pp-top"), scrolled = false;
  function onScroll() {
    var s = scrollY > 24;
    if (s !== scrolled) { scrolled = s; top && top.classList.toggle("is-scrolled", s); }
  }
  addEventListener("scroll", onScroll, { passive: true }); onScroll();

  /* магнитная главная кнопка: до 6 px к курсору, только мышь */
  if (fine && !reduce) {
    doc.querySelectorAll(".pp-btn:not(.line):not(.ink)").forEach(function (b) {
      b.addEventListener("pointermove", function (e) {
        var r = b.getBoundingClientRect(), x = (e.clientX - r.left - r.width / 2) / r.width, y = (e.clientY - r.top - r.height / 2) / r.height;
        b.style.transform = "translate(" + (x * 6).toFixed(1) + "px," + (y * 6).toFixed(1) + "px)";
      });
      b.addEventListener("pointerleave", function () { b.style.transform = ""; });
    });
  }

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

  /* живое поле */
  var c = doc.getElementById("tl-field");
  if (!c || reduce || !c.getContext) return;
  var ctx = c.getContext("2d", { alpha: true }), W, H, dpr, blobs = [], mx = .7, my = .3, tx = .7, ty = .3, raf = 0, last = 0, visible = true;
  var COLORS = [[79, 180, 242], [124, 124, 255], [79, 180, 242], [168, 107, 255]];
  function size() {
    dpr = Math.min(1, devicePixelRatio || 1) * .5;                  /* полразмера: пятна размыты, точность не нужна */
    W = c.width = Math.ceil(innerWidth * dpr); H = c.height = Math.ceil(Math.min(innerHeight, 1200) * dpr);
    c.style.width = innerWidth + "px"; c.style.height = Math.min(innerHeight, 1200) + "px";
  }
  function seed() {
    blobs = COLORS.map(function (col, i) {
      return { col: col, x: .2 + .6 * Math.random(), y: .2 + .6 * Math.random(), r: .28 + .12 * Math.random(), ph: i * 1.7, sp: .12 + .05 * i, pull: .05 + .04 * i };
    });
  }
  function draw(t) {
    raf = 0;
    if (!visible) return;
    if (t - last < 33) { raf = requestAnimationFrame(draw); return; }     /* 30 кадров/с достаточно */
    last = t;
    mx += (tx - mx) * .04; my += (ty - my) * .04;
    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = isLight() ? "multiply" : "lighter";
    var s = t / 1000;
    for (var i = 0; i < blobs.length; i++) {
      var b = blobs[i];
      var bx = b.x + Math.sin(s * b.sp + b.ph) * .08 + (mx - b.x) * b.pull;
      var by = b.y + Math.cos(s * b.sp * .8 + b.ph) * .07 + (my - b.y) * b.pull;
      var br = b.r * (1 + Math.sin(s * .35 + b.ph) * .08) * Math.max(W, H);
      var g = ctx.createRadialGradient(bx * W, by * H, 0, bx * W, by * H, br);
      var a0 = isLight() ? .22 : .16, a1 = isLight() ? .07 : .05;
      g.addColorStop(0, "rgba(" + b.col.join(",") + "," + a0 + ")"); g.addColorStop(.55, "rgba(" + b.col.join(",") + "," + a1 + ")"); g.addColorStop(1, "rgba(" + b.col.join(",") + ",0)");
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    }
    raf = requestAnimationFrame(draw);
  }
  function start() { if (!raf && visible) raf = requestAnimationFrame(draw); }
  size(); seed(); start();
  addEventListener("resize", function () { size(); }, { passive: true });
  addEventListener("pointermove", function (e) { tx = e.clientX / innerWidth; ty = e.clientY / Math.min(innerHeight, 1200); }, { passive: true });
  doc.addEventListener("visibilitychange", function () { visible = doc.visibilityState === "visible"; start(); });
  var heroIO = new IntersectionObserver(function (es) { visible = es[0].isIntersecting && doc.visibilityState === "visible"; start(); });
  heroIO.observe(c);
})();
