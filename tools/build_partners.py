#!/usr/bin/env python3
"""Хаб партнёров /partners/ (заказ MARAFDY, SESSIONS.md 28.09).  python3 tools/build_partners.py

Партнёры — мастера, о которых TimLabs рассказывает бесплатно (решение Тима 26.09): без цен,
мастер о себе — «я», контакт партнёра — его собственный канал записи.
Статьи партнёров (/partners/<id>/<slug>/) делает движок; здесь — только хаб и ссылки на них,
если они уже есть в репозитории.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_hubs import block, read  # noqa: E402

SITE = "https://timlabs.online"
URL = SITE + "/partners/"
PARTNERS = [
    {   # решение Тима 28.09: MARAFDY — только аппаратный массаж, без беременности и доулы
        "id": "marafdy", "name": "MARAFDY", "ic": "🌿", "c": "#35b6ff", "c2": "#9b6cff",
        "tag": "Партнёр · аппаратный массаж",
        "who": "Команда из трёх мастеров, Кисловодск и Кавминводы",
        "about": "Аппаратный массаж с выездом на дом в Кисловодске и на Кавминводах: без масел, в удобное для вас время.",
        "page": "/massage-kislovodsk/", "page_label": "Аппаратный массаж на дому",
        "more": [("https://vk.ru/marafdy", "ВКонтакте"), ("https://dzen.ru/marafdy", "Дзен")],
        "contact": ("https://t.me/MARAFDY_manager", "Записаться у MARAFDY"),
    },
    {   # личная практика Мары — отдельно, без бренда MARAFDY
        "id": "mara-doula", "name": "Доула Мара", "ic": "🤍", "c": "#ff8fd0", "c2": "#35b6ff",
        "tag": "Партнёр · материнство",
        "who": "Мара — доула, личная практика",
        "about": "Подготовка к беременности и родам, сопровождение онлайн и в Кисловодске, восстановление после родов и помощь с кормлением.",
        "page": "/beremennost-i-rody/", "page_label": "Беременность и роды",
        "more": [],
        "contact": ("https://t.me/+d7JxvGJWeaJlYWQy", "Канал Мары в Telegram"),
    },
]


def partner_articles(pid):
    """Статьи партнёра, которые уже выложил движок: /partners/<id>/<slug>/index.html."""
    base = os.path.join(ROOT, "partners", pid)
    out = []
    if os.path.isdir(base):
        for slug in sorted(os.listdir(base)):
            f = os.path.join(base, slug, "index.html")
            if re.fullmatch(r"[a-z0-9-]+", slug) and os.path.exists(f):
                t = re.search(r"<h1[^>]*>(.*?)</h1>", open(f, encoding="utf-8").read(), re.S)
                out.append(("/partners/%s/%s/" % (pid, slug), re.sub(r"<[^>]+>", "", t.group(1)).strip() if t else slug))
    return out


def card(p):
    arts = partner_articles(p["id"])
    chips = ['<a class="chip main" href="%s">%s</a>' % (p["page"], html.escape(p["page_label"]))]
    chips += ['<a class="chip" href="%s"%s>%s</a>' % (u, ' target="_blank" rel="noopener"' if u.startswith("http") else "", html.escape(n)) for u, n in p["more"]]
    chips.append('<a class="chip" style="--c:#2aabee" href="%s" target="_blank" rel="noopener" data-partner="%s">%s</a>'
                 % (p["contact"][0], p["id"], html.escape(p["contact"][1])))
    lst = ""
    if arts:
        lst = '<ul class="alist" style="margin-top:8px">%s</ul>' % "".join(
            '<li><a href="%s">%s</a></li>' % (u, html.escape(n)) for u, n in arts[:6])
    return ('<article class="gcard proj rv" style="--c:{c};--c2:{c2}"><div class="g-top"><span class="g-ic" aria-hidden="true">{ic}</span>'
            '<div><span class="g-tag">{tag}</span><div class="g-who">{who}</div></div></div>'
            '<h3><a href="{page}">{name}</a></h3><p>{about}</p><div class="chips">{chips}</div>{lst}</article>').format(
        c=p["c"], c2=p["c2"], ic=p["ic"], tag=html.escape(p["tag"]), who=html.escape(p["who"]), page=p["page"], name=html.escape(p["name"]),
        about=html.escape(p["about"]), chips="".join(chips), lst=lst)


def main():
    home = read("index.html")
    metrika = block(home, "<!-- Yandex.Metrika counter", "<!-- /Yandex.Metrika counter -->")
    icons = block(home, '<link rel="icon"', 'href="/site.webmanifest">')
    tail = home[home.index("<!-- tl-consent-v2"):home.rindex("</body>")]
    tail = re.sub(r"<!--tl-promo-v1-->.*?</script>\n?", "", tail, flags=re.S)  # всплывающий баннер — только на главной
    footer = block(home, "  <footer>", "</footer>")
    title = "Партнёры TimLabs: проверенные мастера на Кавминводах и онлайн"
    desc = "Мастера, с которыми я работаю и о которых рассказываю: аппаратный массаж на дому в Кисловодске от MARAFDY и сопровождение доулы Мары."
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "TimLabs", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Партнёры", "item": URL}]},
        {"@type": "CollectionPage", "@id": URL, "url": URL, "name": title, "description": desc, "inLanguage": "ru",
         "isPartOf": {"@id": SITE + "/#site"},
         "mainEntity": {"@type": "ItemList", "itemListElement": [
             {"@type": "ListItem", "position": i + 1, "name": p["name"], "url": SITE + p["page"]} for i, p in enumerate(PARTNERS)]}}]}
    page = TEMPLATE.format(title=html.escape(title), desc=html.escape(desc), url=URL, ld=json.dumps(ld, ensure_ascii=False, indent=1),
                           metrika=metrika, icons=icons, cards="\n".join(card(p) for p in PARTNERS), footer=footer, tail=tail)
    os.makedirs(os.path.join(ROOT, "partners"), exist_ok=True)
    open(os.path.join(ROOT, "partners", "index.html"), "w", encoding="utf-8").write(page)
    sm = os.path.join(ROOT, "sitemap.xml")
    s = open(sm, encoding="utf-8").read()
    if URL not in s:
        s = s.replace("</urlset>", "  <url><loc>%s</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n</urlset>" % URL)
        open(sm, "w", encoding="utf-8").write(s)
    print("partners:", len(PARTNERS))


TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#05070e">
<meta property="og:type" content="website">
<meta property="og:site_name" content="TimLabs">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://timlabs.online/avatar.jpg">
<meta property="og:locale" content="ru_RU">
<script type="application/ld+json">
{ld}
</script>
<script>document.documentElement.classList.add("js")</script>
<link rel="stylesheet" href="/assets/tl-glass.css">
<script src="/assets/tl-glass.js" defer></script>
<style>
*{{box-sizing:border-box}}
html{{background:#05070e}}
body{{margin:0;min-height:100vh;color:var(--text);font-family:var(--font-body);line-height:1.55;-webkit-font-smoothing:antialiased;overflow-x:hidden;
  background:radial-gradient(60% 50% at 15% 0%,rgba(0,180,255,.14),transparent 60%),radial-gradient(55% 50% at 90% 100%,rgba(209,0,255,.13),transparent 60%),linear-gradient(180deg,#05070e,#0a0f1c);background-attachment:fixed;background-color:#05070e}}
a{{color:inherit}}
main{{max-width:1080px;margin:0 auto;padding:clamp(22px,5vw,48px) 16px 60px}}
.crumb{{font-size:.8rem;color:var(--dim);margin-bottom:26px}}.crumb a{{color:var(--muted);text-decoration:none}}
.hub-hero{{text-align:center;max-width:720px;margin:0 auto clamp(34px,6vw,56px)}}
.hub-hero h1{{font-family:var(--font-disp);font-size:clamp(2rem,6vw,3.1rem);line-height:1.08;margin:16px 0 14px;letter-spacing:-.015em;
  background:linear-gradient(100deg,#fff 20%,var(--cyan) 60%,var(--magenta));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.hub-hero p{{color:var(--muted);font-size:1.05rem;margin:0 auto;max-width:58ch}}
.note{{color:var(--dim);font-size:.8rem;text-align:center;margin:26px auto 0;max-width:62ch}}
footer{{max-width:760px;margin:40px auto 0;text-align:center;font-size:.7rem;color:var(--dim);line-height:1.6}}footer a{{color:var(--muted)}}
sup{{color:var(--magenta);font-weight:700}}
</style>
{metrika}
<meta name="referrer" content="strict-origin-when-cross-origin">
{icons}
</head>
<body>
<main>
  <nav class="crumb" aria-label="Хлебные крошки"><a href="/">ТимЛабс</a> → Партнёры</nav>
  <header class="hub-hero">
    <span class="tlg-kicker">О наших партнёрах</span>
    <h1>Партнёры TimLabs</h1>
    <p>Мастера, которых я знаю лично и о чьей работе рассказываю. У каждого свои правила записи, стоимость мастер называет сам при обращении.</p>
  </header>
  <section class="tlg-sec" aria-labelledby="p-h">
    <div class="tlg-head rv"><h2 id="p-h">Мастера-партнёры</h2></div>
    <div class="tlg-grid two">
{cards}
    </div>
    <p class="note">Я рассказываю о партнёрах бесплатно и не получаю от них вознаграждения. Услуги партнёров не являются медицинской помощью.</p>
  </section>
{footer}
</main>
{tail}</body>
</html>
"""

if __name__ == "__main__":
    main()
