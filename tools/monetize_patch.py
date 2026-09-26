#!/usr/bin/env python3
"""Патч сайта timlabs.online (26 сен 2026): подбор мастера, подписка, цели Метрики.

Идемпотентен: каждая вставка помечена меткой tl-*-v1 и не дублируется.
Запуск из корня репозитория: python3 tools/monetize_patch.py [--dry]

Юридические рамки (сверено с политикой /privacy/ и 152-ФЗ, 38-ФЗ):
- Подбор НЕ собирает данные на сайте: ответы остаются в браузере и только
  складываются в текст, который человек сам отправляет в мессенджер.
- Цели Метрики уходят, только если Метрика уже загружена (то есть человек
  нажал «Принять»); в параметрах цели — только адрес страницы, без личных данных.
- Цен нет. Рекламных вставок нет (нет вознаграждения от мастеров — не реклама).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry" in sys.argv
SITE = "https://timlabs.online/"
WA = "79938917761"
CHANNEL = "https://t.me/timlabs_journal"

SKIP_DIRS = {"privacy", "consent", "terms", ".git", "tools", "assets", "media"}

SVC = {
    "ekskursii-kislovodsk": "Авторские экскурсии по Кисловодску и КМВ",
    "retrit-otshelnik": "Ретрит «Отшельник» у Железноводска",
    "transformacionnyj-retrit": "Ретрит-центр УМАС",
    "bratstvo-edinomyshlennikov": "Сообщество единомышленников",
    "massage-kislovodsk": "Аппаратный массаж на дому в Кисловодске",
}
# Какие услуги уместны под рубрикой (рубрика берётся из карточек журнала).
RUBRIC_SVC = {
    "Эмоции и психология": ["bratstvo-edinomyshlennikov", "transformacionnyj-retrit"],
    "Развитие": ["bratstvo-edinomyshlennikov", "transformacionnyj-retrit"],
    "Осознанность и ретриты": ["ekskursii-kislovodsk", "retrit-otshelnik"],
}
RETREAT_SLUGS = ("retrit", "yoga")
# Статьи, где предложение услуг неуместно совсем.
NO_SVC = {"doula-smerti"}

# ---------------------------------------------------------------- блоки
PODBOR = r"""<!--tl-podbor-v1--><section class="tlp" id="tl-podbor" aria-labelledby="tlp-h">
<style>
.tlp{margin:28px 0;padding:22px 20px;border:1px solid var(--stroke-hi,rgba(0,180,255,.5));border-radius:16px;background:rgba(0,180,255,.05);color:var(--text,#e7ecf7);text-align:left}
.tlp h2{margin:0 0 6px;font-size:1.25rem}
.tlp p{margin:0 0 12px;color:var(--muted,#9aa3b8);font-size:.95rem;line-height:1.5}
.tlp fieldset{border:0;margin:0 0 12px;padding:0}
.tlp legend{font-weight:600;margin-bottom:8px;font-size:.95rem}
.tlp .tlp-ch{display:flex;flex-wrap:wrap;gap:8px}
.tlp label{cursor:pointer}
.tlp input{position:absolute;opacity:0;pointer-events:none}
.tlp label span{display:inline-block;padding:8px 12px;border:1px solid var(--stroke,rgba(255,255,255,.12));border-radius:999px;font-size:.9rem;transition:border-color .15s,background .15s}
.tlp input:checked+span{border-color:var(--cyan,#00b4ff);background:rgba(0,180,255,.16)}
.tlp input:focus-visible+span{outline:2px solid var(--cyan,#00b4ff);outline-offset:2px}
.tlp .tlp-go{display:flex;flex-wrap:wrap;gap:10px;margin-top:6px}
.tlp .tlp-go a{flex:1 1 200px;text-align:center;padding:12px 16px;border-radius:12px;font-weight:600;text-decoration:none;border:1px solid var(--cyan,#00b4ff);color:var(--text,#e7ecf7)}
.tlp .tlp-go a.tlp-main{background:var(--cyan,#00b4ff);color:#00121f}
.tlp small{display:block;margin-top:10px;color:var(--dim,#5c6478);font-size:.8rem;line-height:1.4}
</style>
<h2 id="tlp-h">Подобрать мастера за минуту</h2>
<p>Отметьте, что вам сейчас нужно, — посоветую специалиста или практику, которые знаю сам.</p>
<fieldset><legend>Что важно сейчас?</legend><div class="tlp-ch">
<label><input type="radio" name="tlp-what" value="беременность и роды"><span>Беременность и роды</span></label>
<label><input type="radio" name="tlp-what" value="тело и восстановление"><span>Тело и восстановление</span></label>
<label><input type="radio" name="tlp-what" value="ретрит или поездка по КМВ"><span>Ретрит или поездка по КМВ</span></label>
<label><input type="radio" name="tlp-what" value="внутренняя опора и сообщество"><span>Внутренняя опора и сообщество</span></label>
<label><input type="radio" name="tlp-what" value="другое"><span>Другое</span></label>
</div></fieldset>
<fieldset><legend>Формат</legend><div class="tlp-ch">
<label><input type="radio" name="tlp-where" value="на месте, Кавминводы"><span>На месте, Кавминводы</span></label>
<label><input type="radio" name="tlp-where" value="онлайн"><span>Онлайн</span></label>
<label><input type="radio" name="tlp-where" value="пока не знаю"><span>Пока не знаю</span></label>
</div></fieldset>
<fieldset><legend>Когда</legend><div class="tlp-ch">
<label><input type="radio" name="tlp-when" value="в ближайшие дни"><span>В ближайшие дни</span></label>
<label><input type="radio" name="tlp-when" value="в этом месяце"><span>В этом месяце</span></label>
<label><input type="radio" name="tlp-when" value="пока присматриваюсь"><span>Пока присматриваюсь</span></label>
</div></fieldset>
<div class="tlp-go">
<a class="tlp-main" data-tlp="wa" href="https://wa.me/__WA__" target="_blank" rel="noopener">Отправить в WhatsApp</a>
<a data-tlp="tg" href="https://t.me/TimLabs_bot?start=podbor" target="_blank" rel="noopener">Подобрать в Telegram-боте</a>
</div>
<small>Ответы не сохраняются на сайте: они только складываются в текст сообщения, и вы сами решаете, отправлять ли его. Не указывайте диагнозы и сведения о здоровье. Подробнее — в <a href="/privacy/">политике обработки данных</a>. Практики мастеров носят велнес-характер и не являются медицинской помощью.</small>
<script>(function(){var box=document.getElementById('tl-podbor');if(!box)return;
function v(n){var x=box.querySelector('input[name="'+n+'"]:checked');return x?x.value:'';}
function text(){var p=['Здравствуйте, Тим! Хочу подобрать мастера.'],a=v('tlp-what'),b=v('tlp-where'),c=v('tlp-when');
if(a)p.push('Что важно: '+a+'.');if(b)p.push('Формат: '+b+'.');if(c)p.push('Когда: '+c+'.');
p.push('Нашёл(ла) вас на странице: '+location.origin+location.pathname);return p.join('\n');}
var wa=box.querySelector('[data-tlp="wa"]');
function ix(n){var l=box.querySelectorAll('input[name=\"'+n+'\"]');for(var i=0;i<l.length;i++)if(l[i].checked)return i+1;return 0;}var tg=box.querySelector('[data-tlp=\"tg\"]');function upd(){wa.href='https://wa.me/__WA__?text='+encodeURIComponent(text());if(tg){var s='podbor',w=ix('tlp-what'),f=ix('tlp-where'),t=ix('tlp-when');if(w)s+='_w'+w;if(f)s+='_f'+f;if(t)s+='_t'+t;tg.href='https://t.me/TimLabs_bot?start='+s;}}
box.addEventListener('change',upd);upd();
box.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('[data-tlp]');if(!a)return;
try{if(typeof ym==='function')ym(111725024,'reachGoal','podbor_send',{via:a.getAttribute('data-tlp'),page:location.pathname});}catch(_){}});
})();</script>
</section>""".replace("__WA__", WA)

SUB = """<!--tl-sub-v1--><div class="tls" style="margin:24px 0;padding:16px 18px;border:1px solid var(--stroke,rgba(255,255,255,.12));border-radius:14px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between">
<span style="flex:1 1 240px;color:var(--text,#e7ecf7)">📬 Новые статьи журнала «Компас» — в Telegram-канале</span>
<a href="%s" target="_blank" rel="noopener" style="padding:10px 16px;border-radius:10px;background:var(--cyan,#00b4ff);color:#00121f;font-weight:600;text-decoration:none">Подписаться</a>
</div>""" % CHANNEL

GOALS = r"""<!--tl-goals-v1--><script>/* цели Метрики: только после согласия (ym есть лишь после «Принять»), без личных данных */
(function(){function g(id,p){try{if(typeof ym==='function')ym(111725024,'reachGoal',id,p||{page:location.pathname});}catch(e){}}
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var h=a.getAttribute('href')||'';
if(/wa\.me|whatsapp\.com/.test(h))g('wa_click');
else if(/t\.me\/timlabs_journal/i.test(h))g('channel_click');
else if(/t\.me\/TimLabs_bot/i.test(h))g('bot_click');
else if(/t\.me\//.test(h))g('tg_click');
else if(/^tel:/.test(h))g('tel_click');
else if(/^mailto:/.test(h))g('mail_click');
else if(/timlabs\.online\/(massage-kislovodsk|ekskursii-kislovodsk|retrit-otshelnik|transformacionnyj-retrit|bratstvo|podgotovka|soprovozhdenie|vosstanovlenie|konsultaciya)/.test(a.href))g('service_click');
else if(a.host&&a.host!==location.host)g('outbound_master');},true);})();</script>"""


DONATE = r"""<!--tl-donate-v1--><a id="tl-donate" href="https://dzen.ru/timlabs.online?donate=true" target="_blank" rel="noopener" aria-label="Поддержать журнал донатом в Дзене">
<span aria-hidden="true">💙</span><span class="tld-t">Поддержать журнал</span><button type="button" class="tld-x" aria-label="Скрыть">×</button></a>
<style>
#tl-donate{position:fixed;left:14px;bottom:14px;z-index:900;display:flex;align-items:center;gap:8px;padding:9px 10px 9px 14px;border-radius:999px;
  font:600 .82rem/1 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#e7ecf7;text-decoration:none;
  background:rgba(12,17,32,.72);border:1px solid rgba(0,180,255,.35);box-shadow:0 8px 28px rgba(0,0,0,.4),0 0 18px rgba(0,180,255,.15);
  -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);opacity:0;transform:translateY(12px);pointer-events:none;transition:opacity .35s,transform .35s,border-color .2s}
#tl-donate.on{opacity:1;transform:none;pointer-events:auto}
#tl-donate:hover{border-color:#d100ff}
#tl-donate:focus-visible{outline:2px solid #00b4ff;outline-offset:3px}
#tl-donate .tld-x{all:unset;cursor:pointer;width:20px;height:20px;display:grid;place-items:center;border-radius:50%;color:#9aa3b8;font-size:1rem}
#tl-donate .tld-x:hover{color:#fff;background:rgba(255,255,255,.1)}
@media (max-width:480px){#tl-donate{font-size:.78rem;padding:8px 8px 8px 12px}}
@media (prefers-reduced-motion:reduce){#tl-donate{transition:none}}
</style>
<script>(function(){var d=document.getElementById('tl-donate');if(!d)return;
function ok(){try{return !!localStorage.getItem('tl-consent-v2')&&!sessionStorage.getItem('tl-donate-off');}catch(e){return true;}}
function upd(){var h=document.documentElement,sc=(h.scrollTop||document.body.scrollTop)/Math.max(1,h.scrollHeight-innerHeight);
d.classList.toggle('on',ok()&&sc>.3&&sc<.97);}
addEventListener('scroll',upd,{passive:true});addEventListener('click',function(){setTimeout(upd,80)});
d.querySelector('.tld-x').addEventListener('click',function(e){e.preventDefault();e.stopPropagation();try{sessionStorage.setItem('tl-donate-off','1')}catch(_){};d.classList.remove('on');});
})();</script>"""


def rubrics():
    t = open(os.path.join(ROOT, "journal/index.html"), encoding="utf-8").read()
    return dict((s, r) for r, s in re.findall(
        r'data-rubric="([^"]*)"><a class="card-link" href="https://timlabs\.online/journal/([^"/]+)/"', t))


def fix_related(slug, rubric, html):
    m = re.search(r'(<div class="rel-list">)(.*?)(</div>)', html, re.S)
    if not m:
        return html, False
    links = re.findall(r'<a href="([^"]*)">([^<]*)</a>', m.group(2))
    svc_re = re.compile(r'^https://timlabs\.online/(%s)/$' % "|".join(
        ["massage-kislovodsk", "ekskursii-kislovodsk", "retrit-otshelnik", "transformacionnyj-retrit",
         "bratstvo-edinomyshlennikov", "podgotovka-k-rodam", "podgotovka-k-beremennosti",
         "soprovozhdenie-beremennosti-onlayn", "vosstanovlenie-posle-rodov", "konsultaciya-grudnoe-vskarmlivanie"]))
    had_svc = any(svc_re.match(h) for h, _ in links)
    keep = [(h, a) for h, a in links if not svc_re.match(h)]
    if slug in NO_SVC:
        svc = []
    elif rubric in RUBRIC_SVC:
        svc = ["transformacionnyj-retrit", "retrit-otshelnik"] if (
            rubric == "Осознанность и ретриты" and any(k in slug for k in RETREAT_SLUGS)) else RUBRIC_SVC[rubric]
        svc = [(SITE + s + "/", SVC[s]) for s in svc] if had_svc else []
    else:  # рубрики, где услуги уже по смыслу: только убрать дубли
        svc = [(h, a) for h, a in links if svc_re.match(h)]
    out, seen = [], set()
    for h, a in keep[:1] + svc + keep[1:]:
        if h in seen:
            continue
        seen.add(h)
        out.append('<a href="%s">%s</a>' % (h, a))
    new = m.group(1) + "".join(out) + m.group(3)
    if new == m.group(0):
        return html, False
    return html[:m.start()] + new + html[m.end():], True


def insert_before_body(html, block):
    i = html.rfind("</body>")
    return html if i < 0 else html[:i] + block + "\n" + html[i:]


def main():
    rub = rubrics()
    stats = {"consent": 0, "related": 0, "podbor": 0, "sub": 0, "goals": 0, "utm": 0, "files": 0}
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        if "index.html" not in fns:
            continue
        p = os.path.join(dp, "index.html")
        rel = os.path.relpath(p, ROOT)
        h = open(p, encoding="utf-8").read()
        if re.search(r"<title>(Материал перенесён|Страница удалена)", h):
            continue
        o = h
        # 1. согласие не сохранялось (ключом было само значение)
        if "localStorage.setItem(v,v)" in h:
            h = h.replace("localStorage.setItem(v,v)", "localStorage.setItem(KEY,v)")
            stats["consent"] += 1
        is_article = rel.startswith("journal/") and rel != "journal/index.html"
        if is_article:
            slug = rel.split("/")[1]
            h, ch = fix_related(slug, rub.get(slug, ""), h)
            stats["related"] += ch
            if "<!--tl-sub-v1-->" not in h:
                anchor = h.find('<p class="disclaimer">')
                if anchor > 0:
                    h = h[:anchor] + SUB + "\n  " + h[anchor:]
                    stats["sub"] += 1
            if "<!--tl-podbor-v1-->" not in h and slug not in NO_SVC:
                anchor = h.find('<section class="related">')
                if anchor < 0:
                    anchor = h.find('<p class="disclaimer">')
                if anchor > 0:
                    h = h[:anchor] + PODBOR + "\n\n  " + h[anchor:]
                    stats["podbor"] += 1
        if rel == "index.html":
            if "<!--tl-podbor-v1-->" not in h:
                a = h.find('<div class="cta-row">', h.find('id="p-care"'))
                if a > 0:
                    h = h[:a] + PODBOR + "\n      " + h[a:]
                    stats["podbor"] += 1
            if 'href="#tl-podbor"' not in h:
                h = h.replace('<div class="hero-cta">',
                              '<div class="hero-cta">\n      <a class="btn" href="#tl-podbor">Подобрать мастера за минуту</a>', 1)
            for site in ("https://ramagor.ru", "https://marafdi.clients.site/"):
                new = site + ("&" if "?" in site else "?") + "utm_source=timlabs&utm_medium=referral&utm_campaign=home"
                if 'href="%s"' % site in h:
                    h = h.replace('href="%s"' % site, 'href="%s"' % new)
                    stats["utm"] += 1
        if "<!--tl-donate-v1-->" not in h:
            h = insert_before_body(h, DONATE)
            stats["donate"] = stats.get("donate", 0) + 1
        if "<!--tl-goals-v1-->" not in h:
            h = insert_before_body(h, GOALS)
            stats["goals"] += h != o
        if h != o:
            stats["files"] += 1
            if not DRY:
                open(p, "w", encoding="utf-8").write(h)
    print(stats)


if __name__ == "__main__":
    main()
