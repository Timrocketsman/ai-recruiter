/* TimLabs: essential consent preference; analytics requires explicit permission. */
(function () {
  'use strict';
  if (window.__tlConsentReady) return;
  var box = document.getElementById('tl-consent');
  if (!box) return;
  window.__tlConsentReady = true;
  var KEY = 'tl-consent-v2', REFUSAL = 'tl-consent-refused';
  var writable = false, choice = null, channel = null;
  try {
    var probe = '__tl-consent-probe', prior = localStorage.getItem(probe);
    localStorage.setItem(probe, '1');
    writable = localStorage.getItem(probe) === '1';
    if (prior === null) localStorage.removeItem(probe);
    else localStorage.setItem(probe, prior);
  } catch (_) { writable = false; }
  function refusedHere() {
    try { return sessionStorage.getItem(REFUSAL) === '1'; }
    catch (_) { return false; }
  }
  function stored() {
    if (refusedHere()) return 'declined';
    if (!writable) return null;
    try {
      var value = localStorage.getItem(KEY);
      return value === 'accepted' || value === 'declined' ? value : null;
    } catch (_) { writable = false; return null; }
  }
  choice = stored();
  window.tlConsentAllowed = function () { return choice === 'accepted'; };
  var legal = /^\/(privacy|consent|terms)(\/|$)/.test(location.pathname);
  var veil = document.getElementById('tl-consent-veil');
  var opened = false, previousFocus = null, inerted = [], oldPadding = '';
  var status = document.createElement('p');
  status.id = 'tl-consent-status'; status.setAttribute('role', 'status');
  box.appendChild(status);
  var done = document.createElement('button');
  done.type = 'button'; done.textContent = 'Готово'; done.hidden = true;
  done.addEventListener('click', hide); box.appendChild(done);
  function message(text) { status.textContent = text; done.hidden = !text; }
  function focusable() {
    return Array.prototype.filter.call(box.querySelectorAll(
      'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'
    ), function (el) { return el.getClientRects().length && !el.closest('[inert]'); });
  }
  function focusFirst() {
    var items = focusable();
    if (items.length) items[0].focus();
    else { box.setAttribute('tabindex', '-1'); box.focus(); }
  }
  function lock(on) {
    if (veil) veil.classList.toggle('show', on);
    document.body.classList.toggle('tl-consent-lock', on);
    if (on) {
      var current = box;
      while (current && current !== document.body) {
        var parent = current.parentElement;
        if (!parent) break;
        Array.prototype.forEach.call(parent.children, function (el) {
          if (el !== current && el !== veil && !/^(SCRIPT|STYLE|LINK|META)$/.test(el.tagName)) {
            inerted.push([el, el.inert]); el.inert = true;
          }
        });
        current = parent;
      }
    } else {
      inerted.forEach(function (entry) { entry[0].inert = entry[1]; });
      inerted = [];
    }
  }
  function show(fromSettings) {
    if (opened) return;
    opened = true; previousFocus = document.activeElement;
    oldPadding = document.body.style.paddingBottom;
    box.classList.add('show');
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', legal ? 'false' : 'true');
    if (!box.hasAttribute('aria-label') && !box.hasAttribute('aria-labelledby'))
      box.setAttribute('aria-label', 'Настройки обработки данных');
    if (legal) document.body.style.paddingBottom = '240px';
    else lock(true);
    if (!legal || fromSettings) focusFirst();
  }
  function hide() {
    if (!opened) return;
    opened = false; box.classList.remove('show');
    document.body.style.paddingBottom = oldPadding; lock(false);
    if (previousFocus && previousFocus.isConnected && !previousFocus.closest('[inert]'))
      previousFocus.focus();
  }
  function start() {
    if (choice === 'accepted' && typeof window.tlLoadMetrika === 'function') window.tlLoadMetrika();
  }
  function stop() {
    try {
      if (typeof window.tlStopMetrika === 'function') window.tlStopMetrika();
      return true;
    } catch (error) {
      window.__tlConsentErrors = window.__tlConsentErrors || [];
      window.__tlConsentErrors.push({code:'metrika_stop_failed', at:Date.now(), name:String(error.name || 'Error')});
      console.error('TimLabs: metrika_stop_failed');
      return false;
    }
  }
  function rememberRefusal() {
    // Session veto survives navigation even if the durable write fails once.
    try { sessionStorage.setItem(REFUSAL, '1'); } catch (_) {}
    try {
      localStorage.setItem(KEY, 'declined');
      if (localStorage.getItem(KEY) === 'declined') return true;
    } catch (_) {}
    // Never leave an old accepted value silently authoritative after a failed write.
    try {
      localStorage.removeItem(KEY);
      return localStorage.getItem(KEY) === null;
    } catch (_) { return false; }
  }
  function choose(value) {
    choice = value;
    if (value === 'declined') {
      // Persist and notify before touching third-party code: teardown may throw.
      var saved = rememberRefusal();
      try { if (channel) channel.postMessage('declined'); } catch (_) {}
      var stopped = stop();
      if (!saved || !stopped) {
        message(!stopped ? 'Вы отказались от статистики. Счётчик не подтвердил остановку: закройте эту вкладку.' +
          (!saved ? ' Браузер также не сохранил выбор; закройте другие вкладки сайта.' : '') :
          'Статистика отключена в этой вкладке. Браузер не сохранил выбор; закройте другие вкладки сайта.');
        done.focus();
        return;
      }
    } else {
      try {
        localStorage.setItem(KEY, 'accepted');
        if (localStorage.getItem(KEY) === 'accepted') {
          writable = true; sessionStorage.removeItem(REFUSAL);
        }
      } catch (_) {}
      start();
      if (window.__tlMetrikaRevoked) {
        message('Выбор сохранён. Статистика включится при следующем переходе по сайту.');
        done.focus();
        return;
      }
    }
    message(''); hide();
  }
  var ok = document.getElementById('tl-consent-ok'), no = document.getElementById('tl-consent-no');
  if (ok) ok.addEventListener('click', function () { choose('accepted'); });
  if (no) no.addEventListener('click', function () { choose('declined'); });
  document.addEventListener('click', function (event) {
    var target = event.target && event.target.closest && event.target.closest('#tl-consent-settings');
    if (target) { event.preventDefault(); message(''); show(true); }
  });
  document.addEventListener('keydown', function (event) {
    if (!opened || legal || event.key !== 'Tab') return;
    var items = focusable();
    if (!items.length) { event.preventDefault(); box.focus(); return; }
    var first = items[0], last = items[items.length - 1];
    if (event.shiftKey && (document.activeElement === first || !box.contains(document.activeElement))) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !box.contains(document.activeElement))) {
      event.preventDefault(); first.focus();
    }
  });
  function externalRefusal() {
    choice = 'declined'; try { sessionStorage.setItem(REFUSAL, '1'); } catch (_) {}
    if (stop()) hide();
    else {
      show(false);
      message('Вы отказались от статистики в другой вкладке. Счётчик не подтвердил остановку: закройте эту вкладку.');
      done.focus();
    }
  }
  window.addEventListener('storage', function (event) {
    if (event.key !== KEY && event.key !== null) return;
    // A durable withdrawal overrides every currently open tab's memory choice.
    var value = null;
    try { value = localStorage.getItem(KEY); } catch (_) {}
    if (value !== 'accepted') {
      externalRefusal();
    }
    // Acceptance in another tab never overrides this tab's previous refusal.
  });
  try {
    channel = new BroadcastChannel('tl-consent');
    channel.onmessage = function (event) {
      if (event.data !== 'declined') return;
      externalRefusal();
    };
  } catch (_) {}
  function reconcileAfterResume() {
    // Frozen/background documents may miss storage or broadcast notifications.
    if (choice === 'accepted' && stored() !== 'accepted') externalRefusal();
  }
  window.addEventListener('pageshow', reconcileAfterResume);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') reconcileAfterResume();
  });
  if (choice === null) show(false);
  start();
})();
