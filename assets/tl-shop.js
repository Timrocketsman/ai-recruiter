/* TimLabs — магазин /magazin/: корзина и заказ через Telegram (27.10.2026, на основе слоя shop-min).
   Позиции: p — цена (null = «по запросу»), f — цена «от», u — единица («в месяц»), q — сколько можно положить, i — обложка, h — страница.
   Движение — только примитивы window.TL из tl-motion.js: TL.spring, TL.Handle, TL.tick. Своего requestAnimationFrame нет, @keyframes нет.
   Без этого файла магазин работает: у каждой карточки ссылка «Заказать в Telegram» на один товар. */
(function () {
  "use strict";
  var doc = document, body = doc.body, TL = window.TL;
  if (!TL || !TL.spring || !TL.tick) return;           /* без tl-motion.js — остаются ссылки на бота */

  /* каталог для корзины: JSON-блок #sh-catalog на каждой странице */
  var CAT = {}, ORDER = [];
  try {
    var raw = JSON.parse(doc.getElementById("sh-catalog").textContent);
    for (var k in raw) if (/^[A-Za-z0-9]{2,4}$/.test(k)) { CAT[k] = raw[k]; ORDER.push(k); }
  } catch (e) { return; }
  var BOT = body.getAttribute("data-bot") || "";
  var KEY = "tl-shop-cart-v2", cart = {};
  function mx(i) { return (CAT[i] && CAT[i].q) || 1; }

  /* ── хранилище: всё в try/catch; без него корзина живёт до перезагрузки ── */
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || "{}");
    for (var id in saved) if (CAT[id]) { var n = parseInt(saved[id], 10); if (n > 0) cart[id] = Math.min(mx(id), n); }
  } catch (e) {}
  function save() { try { localStorage.setItem(KEY, JSON.stringify(cart)); } catch (e) {} }

  function rub(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function ids() { return ORDER.filter(function (i) { return cart[i] > 0; }); }
  function count() { return ids().reduce(function (s, i) { return s + cart[i]; }, 0); }
  function total() { return ids().reduce(function (s, i) { return s + (CAT[i].p == null ? 0 : cart[i] * CAT[i].p); }, 0); }
  function money(b, q) { return b.p == null ? "по запросу" : (b.f ? "от " : "") + rub(b.p * q) + (b.u || ""); }
  function totalText() {
    var s = total(), fr = ids().some(function (i) { return CAT[i].p != null && CAT[i].f; }), ask = ids().some(function (i) { return CAT[i].p == null; });
    if (!s) return "по запросу";
    return (fr ? "от " : "") + rub(s) + (ask ? " + по запросу" : "");
  }

  /* ── код заказа: пары <id><кол-во>, [A-Za-z0-9_-], весь параметр start ≤ 64 символов; иначе null ── */
  function startParam() {
    var c = ids().map(function (i) { return i + cart[i]; }).join(""), p = "o_" + c;
    return c && /^[A-Za-z0-9_-]+$/.test(p) && p.length <= 64 ? p : null;
  }
  function orderLink() { var p = startParam(); return "https://t.me/" + BOT + "?start=" + (p || "shop"); }
  function orderText() {
    return "Заказ: " + ids().map(function (i) { return CAT[i].t + (cart[i] > 1 ? " × " + cart[i] : "") + " — " + money(CAT[i], cart[i]); }).join("; ") + ", итого " + totalText();
  }
  function copy(text) {
    function legacy() {
      var ta = doc.createElement("textarea"); ta.value = text; ta.setAttribute("readonly", ""); ta.className = "sh-sr"; body.appendChild(ta);
      ta.select(); var ok = false; try { ok = doc.execCommand("copy"); } catch (e) {} ta.remove(); return ok;
    }
    try { if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text).then(function () { return true; }, legacy); } catch (e) {}
    return Promise.resolve(legacy());
  }

  /* ── живой регион для экранных дикторов ── */
  var live = doc.createElement("p"); live.className = "sh-sr"; live.setAttribute("aria-live", "polite"); body.appendChild(live);
  function say(t) { live.textContent = ""; setTimeout(function () { live.textContent = t; }, 30); }

  /* смена текста кнопки: opacity .2 → 1 за 180 мс (класс is-swap снимается через кадр общего цикла) */
  function swap(btn, text) {
    btn.classList.add("is-swap"); btn.textContent = text;
    var n = 0; TL.tick.add(function back() { if (++n < 2) return; TL.tick.remove(back); btn.classList.remove("is-swap"); });
  }

  /* ── кнопка корзины и счётчик ── */
  var cartBtn = doc.querySelector(".sh-cart-btn");
  if (!cartBtn) {                                      /* шапка — общая для сайта (journal_v2.TOP), кнопку корзины ставит магазин сам */
    var wrap = doc.querySelector(".pp-top .pp-wrap"); if (!wrap) return;
    cartBtn = doc.createElement("button"); cartBtn.type = "button"; cartBtn.className = "sh-cart-btn";
    cartBtn.setAttribute("aria-controls", "sh-cart"); cartBtn.setAttribute("aria-expanded", "false"); cartBtn.setAttribute("aria-label", "Корзина, товаров: 0");
    cartBtn.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6.331 8h11.339a2 2 0 0 1 1.977 2.304l-1.255 8.152a3 3 0 0 1 -2.966 2.544h-6.852a3 3 0 0 1 -2.965 -2.544l-1.255 -8.152a2 2 0 0 1 1.977 -2.304z"/><path d="M9 11v-5a3 3 0 0 1 6 0v5"/></svg><span class="sh-count is-zero" aria-hidden="true">0</span>';
    var menu = wrap.querySelector(".pp-menu"); wrap.insertBefore(cartBtn, menu || null);
  }
  var countEl = cartBtn.querySelector(".sh-count");
  cartBtn.hidden = false;
  var bump = TL.spring({ from: 1, onUpdate: function (v) { countEl.style.transform = v === 1 ? "" : "scale(" + v.toFixed(3) + ")"; } });
  function pulse() {                                    /* пружина 170/26: цель 1.15 и сразу обратно в 1 (≈ 240 мс) */
    bump.set(1.15);
    var n = 0; TL.tick.add(function back() { if (++n < 5) return; TL.tick.remove(back); bump.set(1); });
  }

  /* ── корзина: панель, вуаль ── */
  var X = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M18 6l-12 12"/><path d="M6 6l12 12"/></svg>';
  var MINUS = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M5 12h14"/></svg>';
  var PLUS = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M12 5v14"/><path d="M5 12h14"/></svg>';
  var veil = doc.createElement("div"); veil.className = "sh-veil"; veil.setAttribute("aria-hidden", "true");
  var drawer = doc.createElement("aside");
  drawer.id = "sh-cart"; drawer.className = "sh-drawer";
  drawer.setAttribute("role", "dialog"); drawer.setAttribute("aria-modal", "true"); drawer.setAttribute("aria-labelledby", "sh-cart-h");
  drawer.setAttribute("inert", "");
  drawer.innerHTML =
    '<div class="sh-head"><h2 id="sh-cart-h" tabindex="-1">Корзина</h2><button class="sh-x" type="button" data-close aria-label="Закрыть корзину">' + X + '</button></div>' +
    '<ul class="sh-lines"></ul><p class="sh-empty" hidden>Пока пусто — добавьте товар из каталога</p>' +
    '<div class="sh-foot" hidden><p class="sh-total"><span>Итого</span><b></b></p>' +
    '<p class="sh-note">' + esc(body.getAttribute("data-note") || "Оплата — после подтверждения в Telegram.") + '</p>' +
    '<a class="pp-btn sh-go" href="https://t.me/' + esc(BOT) + '" rel="noopener">Оформить в Telegram</a>' +
    '<button class="sh-copy" type="button">Скопировать заказ</button></div>';
  body.appendChild(veil); body.appendChild(drawer);
  var head = drawer.querySelector("#sh-cart-h"), list = drawer.querySelector(".sh-lines"), empty = drawer.querySelector(".sh-empty"),
    foot = drawer.querySelector(".sh-foot"), sumEl = foot.querySelector(".sh-total b"), go = foot.querySelector(".sh-go"), copyBtn = foot.querySelector(".sh-copy");

  function render(focusSel) {
    var list_ = ids(), n = count();
    countEl.textContent = n; countEl.classList.toggle("is-zero", n === 0);
    cartBtn.setAttribute("aria-label", "Корзина, товаров: " + n);
    list.innerHTML = list_.map(function (i) {
      var b = CAT[i], q = cart[i];
      var pic = b.i ? '<img src="' + esc(b.i) + '" width="64" height="80" alt="' + esc(b.t) + ' — обложка" loading="lazy" decoding="async">'
        : '<span class="sh-line-ic" aria-hidden="true">' + esc(b.t.replace(/[«»"]/g, "").charAt(0)) + '</span>';
      return '<li class="sh-line" data-id="' + i + '">' + pic +
        '<div><p class="sh-line-t"><a href="' + esc(b.h) + '">' + esc(b.t) + '</a></p><p class="sh-line-u">' + money(b, 1) + (mx(i) > 1 && b.p != null ? ' за штуку' : '') + '</p></div>' +
        '<div class="sh-line-r"><div class="sh-qty" role="group" aria-label="Количество: ' + esc(b.t) + '">' +
        '<button type="button" data-dec="' + i + '" aria-label="Убрать один">' + MINUS + '</button><output aria-live="polite">' + q + '</output>' +
        (mx(i) > 1 ? '<button type="button" data-inc="' + i + '" aria-label="Добавить ещё один"' + (q >= mx(i) ? " disabled" : "") + '>' + PLUS + '</button>' : '') + '</div>' +
        '<b class="sh-line-s">' + money(b, q) + '</b></div></li>';
    }).join("");
    list.hidden = !list_.length; empty.hidden = !!list_.length; foot.hidden = !list_.length;
    sumEl.textContent = totalText();
    go.href = orderLink();
    if (focusSel) { var f = drawer.querySelector(focusSel); (f && !f.disabled ? f : head).focus({ preventScroll: true }); }
  }

  /* ── открыть / закрыть: фокус на заголовок и обратно на кнопку, body без прокрутки ── */
  var isOpen = false;
  function open() {
    if (isOpen) return; isOpen = true;
    snap[1] = drawer.offsetWidth || 420;
    drawer.removeAttribute("inert"); drawer.style.transform = "";
    drawer.classList.add("open"); veil.classList.add("open");
    body.classList.add("sh-lock"); cartBtn.setAttribute("aria-expanded", "true");
    head.focus({ preventScroll: true });
  }
  function close() {
    if (!isOpen) return; isOpen = false;
    drawer.classList.remove("open"); veil.classList.remove("open");
    drawer.setAttribute("inert", ""); body.classList.remove("sh-lock"); cartBtn.setAttribute("aria-expanded", "false");
    cartBtn.focus({ preventScroll: true });
  }
  cartBtn.addEventListener("click", function () { render(); open(); });
  veil.addEventListener("click", close);
  doc.addEventListener("keydown", function (e) {
    if (!isOpen) return;
    if (e.key === "Escape") { e.preventDefault(); close(); return; }
    if (e.key === "Tab") {                              /* фокус не уходит из диалога */
      var f = [].filter.call(drawer.querySelectorAll("button:not([disabled]),a[href],[tabindex='-1']#sh-cart-h"), function (el) { return el.offsetParent !== null || el === head; });
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && doc.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && doc.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  drawer.addEventListener("click", function (e) {
    var t = e.target.closest("button"); if (!t) return;
    if (t.hasAttribute("data-close")) { close(); return; }
    if (t === copyBtn) { doCopy(); return; }
    var inc = t.getAttribute("data-inc"), dec = t.getAttribute("data-dec");
    if (inc && CAT[inc]) { cart[inc] = Math.min(mx(inc), (cart[inc] || 0) + 1); save(); render('[data-inc="' + inc + '"]'); }
    else if (dec && CAT[dec]) {
      cart[dec] = (cart[dec] || 0) - 1;
      if (cart[dec] <= 0) { delete cart[dec]; save(); render(); head.focus({ preventScroll: true }); say("Товар убран из корзины"); }
      else { save(); render('[data-dec="' + dec + '"]'); }
    }
  });
  function doCopy() {
    copy(orderText()).then(function (ok) {
      var was = "Скопировать заказ";
      copyBtn.textContent = ok ? "Заказ скопирован" : "Не удалось скопировать";
      say(copyBtn.textContent);
      setTimeout(function () { copyBtn.textContent = was; }, 1200);
    });
  }
  /* код не влез в 64 символа — бот открывается без кода, заказ копируется текстом */
  go.addEventListener("click", function () { if (!startParam() && ids().length) copy(orderText()); });

  /* ── свайп вправо: TL.Handle по оси x, порог 30 % ширины, иначе пружина возвращает ── */
  var snap = [0, 420], dragging = false;
  var handle = TL.Handle(drawer, {
    axis: "x", min: 0, max: 4000, snap: snap,
    onRelease: function (v) { if (v >= snap[1] - 1) finishClose(); else settle(); }
  });
  drawer.style.transform = "";                          /* Handle ставит translateX(0) сразу — сдвиг держит CSS, пока нет перетаскивания */
  function settle() { dragging = false; drawer.classList.remove("is-drag"); drawer.style.transform = ""; }
  function finishClose() {
    drawer.classList.remove("open");                    /* is-drag ещё стоит: класс и инлайн-сдвиг совпадают, скачка нет */
    drawer.style.transform = "";
    var n = 0; TL.tick.add(function off() { if (++n < 2) return; TL.tick.remove(off); dragging = false; drawer.classList.remove("is-drag"); });
    isOpen = true; close();
  }
  drawer.addEventListener("pointerdown", function (e) {
    if (e.button > 0 || e.target.closest("button,a,input,output")) { e.stopPropagation(); return; }  /* кнопки и ссылки внутри — не ручка */
    dragging = true; drawer.classList.add("is-drag");
  }, true);
  drawer.addEventListener("keydown", function (e) { if (/^Arrow/.test(e.key) && e.target !== drawer) e.stopPropagation(); }, true);
  function release() {
    if (!dragging) return;
    var w = snap[1], v = handle.value();
    if (TL.reduce) { if (v > w * 0.3) finishClose(); else settle(); return; }
    handle.set(v > w * 0.3 ? w : 0);
  }
  drawer.addEventListener("pointerup", release);
  drawer.addEventListener("pointercancel", release);

  /* ── «Заказать в Telegram» → «В корзину» ── */
  var timers = new WeakMap();
  doc.querySelectorAll("a[data-add]").forEach(function (a) {
    var id = a.getAttribute("data-add"); if (!CAT[id]) return;
    var b = doc.createElement("button");
    b.type = "button"; b.className = a.className; b.setAttribute("data-add", id); b.textContent = "В корзину";
    b.setAttribute("aria-label", "В корзину: " + CAT[id].t);
    a.replaceWith(b);
    b.addEventListener("click", function () {
      cart[id] = Math.min(mx(id), (cart[id] || 0) + 1); save(); render(); pulse();
      say("Добавлено в корзину: " + CAT[id].t + ", товаров: " + count());
      clearTimeout(timers.get(b));
      swap(b, "✓ В корзине");
      timers.set(b, setTimeout(function () { swap(b, "В корзину"); }, 1200));
    });
  });

  /* ── фильтры: таблетки прячут чужие карточки атрибутом hidden, контент остаётся в DOM ── */
  var chips = doc.querySelectorAll(".sh-chip[data-filter]"), cards = doc.querySelectorAll(".sh-card"), groups = doc.querySelectorAll(".sh-group");
  chips.forEach(function (c) {
    c.addEventListener("click", function (e) {
      e.preventDefault();
      var f = c.getAttribute("data-filter");
      chips.forEach(function (x) { if (x === c) x.setAttribute("aria-current", "true"); else x.removeAttribute("aria-current"); });
      cards.forEach(function (k) { k.hidden = f !== "all" && k.getAttribute("data-cat") !== f; });
      groups.forEach(function (g) { g.hidden = !g.querySelector(".sh-card:not([hidden])"); });
      try { history.replaceState(null, "", c.getAttribute("href")); } catch (er) {}
    });
  });

  /* ── появление карточек: ступенька 70 мс (≤ 6 в группе); ≥ 901 px — из расфокуса (.rv-focus core) ──
     СЛОЙ: не хватило — tl-motion.js раздаёт ступеньку и rv-focus только .pp-bento/.pj-grid/…; для .sh-grid это делается здесь */
  doc.querySelectorAll(".sh-grid").forEach(function (g) {
    var kids = g.querySelectorAll(":scope > .rv");
    for (var i = 0; i < kids.length && i < 6; i++) kids[i].style.transitionDelay = (i * 70) + "ms";
  });
  if (!TL.reduce && matchMedia("(min-width: 901px)").matches && TL.relay && TL.relay("focus")) {
    doc.querySelectorAll(".sh-card.rv:not(.in)").forEach(function (el) {
      el.classList.add("rv-focus");
      el.addEventListener("transitionend", function done(e) {
        if (e.propertyName !== "opacity") return;
        el.classList.remove("rv-focus"); el.style.transitionDelay = ""; el.removeEventListener("transitionend", done);
      });
    });
  }

  render();
})();
