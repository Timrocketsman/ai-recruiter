#!/usr/bin/env python3
"""Страницы направлений timlabs.online: /beremennost-i-rody/, /telo-i-vosstanovlenie/, /retrity-i-kmv/.

Списки статей берутся из journal/index.html (рубрика + слова в адресе), поэтому
скрипт можно перезапускать после выхода новых статей:  python3 tools/build_hubs.py
Общие блоки (Метрика, согласие, скрепка, цели) копируются с главной — один источник правды.
Правила сайта: цен нет, чужих ссылок нет, медицинских обещаний нет, Instagram со сноской.
"""
import html
from pathlib import Path
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://timlabs.online"


def read(p):
    return Path(os.path.join(ROOT, p)).read_text(encoding="utf-8")


def articles():
    t = read("journal/index.html")
    legacy = re.findall(
        r'data-rubric="([^"]*)"><a class="card-link" href="https://timlabs\.online/journal/([^"/]+)/"><h2 class="card-title">([^<]*)</h2></a>'
        r'<div class="card-meta"><span class="card-rubric">[^<]*</span><span class="card-date">([^<]*)', t)
    return legacy if legacy else current_journal_articles(t)




def current_journal_articles(text):
    """Current pj-card DOM, deduplicated; retain the supported legacy format."""
    from html.parser import HTMLParser
    class Cards(HTMLParser):
        def __init__(self):
            super().__init__(); self.row = None; self.heading = False; self.rows = []; self.seen = set()
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag == "article" and "pj-card" in a.get("class", "").split():
                self.row = {"rubric": a.get("data-rubric", ""), "title": [], "date": "", "slug": None}
            if self.row is None: return
            if tag in ("h2", "h3"): self.heading = True
            if tag == "a" and self.heading:
                m = re.fullmatch(r"(?:https://timlabs\.online)?/journal/([a-z0-9-]+)/", a.get("href", ""))
                if m: self.row["slug"] = m[1]
            if tag == "time": self.row["date"] = a.get("datetime", "")
        def handle_data(self, data):
            if self.row is not None and self.heading: self.row["title"].append(data)
        def handle_endtag(self, tag):
            if tag in ("h2", "h3"): self.heading = False
            if tag == "article" and self.row is not None:
                r = self.row; title = " ".join("".join(r["title"]).split())
                if r["slug"] and title and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]) and r["slug"] not in self.seen:
                    self.seen.add(r["slug"]); self.rows.append((r["rubric"], r["slug"], title, r["date"]))
                self.row = None
    p = Cards(); p.feed(text); p.close()
    if not p.rows: raise ValueError("journal card structure unsupported; refusing empty hub lists")
    return p.rows


def native_hub_page(generated, previous, shared, kind="hub"):
    """Keep approved head/static copy; rebuild only owner-controlled lists.

    Current published pages provide the real shared shell, not guard markers.
    New pages get the same actual navigation/assets/theme/motion from the journal.
    """
    if previous:
        for pattern in (r'<head\b[^>]*>.*?</head>', r'<header class="pp-top">.*?</header>'):
            if len(re.findall(pattern, previous, re.S)) != 1: raise ValueError("approved hub shell missing")
        canonical = lambda h: re.search(r'<link rel="canonical" href="([^"]+)"', h)[1]
        if canonical(previous) != canonical(generated): raise ValueError("hub canonical changed")
        if kind == "hub":
            pattern = r'<section\b[^>]*\bid="stati"[^>]*>.*?</section>'
            old = re.search(pattern, previous, re.S); new = re.search(pattern, generated, re.S)
            if old is None or new is None: raise ValueError("owned article-list section missing")
            return previous[:old.start()] + new[0] + previous[old.end():]
        pattern = r'<article\b[^>]*\bgcard[^>]*>.*?</article>'
        fresh = {}
        for match in re.finditer(pattern, generated, re.S):
            key = re.search(r'<h3><a href="([^"]+)"', match[0])
            if key: fresh[key[1]] = match[0]
        seen = set()
        def update(match):
            old = match[0]; key = re.search(r'<h3><a href="([^"]+)"', old)
            if key is None or key[1] not in fresh: raise ValueError("approved partner cards changed")
            seen.add(key[1]); current = fresh[key[1]]
            pat = r'<ul class="alist"[^>]*>.*?</ul>'
            new_list = re.search(pat, current, re.S); old_list = re.search(pat, old, re.S)
            if old_list: return old[:old_list.start()] + (new_list[0] if new_list else "") + old[old_list.end():]
            return old.replace("</article>", (new_list[0] if new_list else "") + "</article>", 1)
        result = re.sub(pattern, update, previous, flags=re.S)
        if seen != set(fresh): raise ValueError("new partner requires approved template update")
        return result
    # Genuine first render: shared production assets/nav/theme/runtime, no new library.
    header = re.search(r'<header class="pp-top">.*?</header>', shared, re.S)
    motion = re.search(r'<script[^>]*src="/assets/tl-motion\.js[^>]*>.*?</script>', shared, re.S)
    theme = next((x for x in re.findall(r'<script\b[^>]*>.*?</script>', shared, re.S) if 'localStorage.getItem("tl-theme")' in x), None)
    if header is None or motion is None or theme is None: raise ValueError("shared production frame incomplete")
    page = re.sub(r'<(?:link|script)\b[^>]*(?:tl-glass\.css|tl-glass\.js)[^>]*>(?:</script>)?', "", generated)
    styles = []
    for name in ("tl-paper", "tl-journal", "tl-site"):
        match = re.search(r'<link[^>]*href="/assets/' + name + r'\.css[^>]*>', shared)
        styles.append(match[0] if match else '<link rel="stylesheet" href="/assets/' + name + '.css">')
    theme_colors = re.findall(r'<meta[^>]*name="theme-color"[^>]*>', shared)
    preloads = re.findall(r'<link[^>]*rel="preload"[^>]*href="/assets/fonts/[^>]*>', shared)
    page = re.sub(r'<meta[^>]*name="theme-color"[^>]*>', "", page)
    page = page.replace("</head>", "\n".join(theme_colors + [theme] + preloads + styles) + "\n</head>", 1)
    page = page.replace("<body>", '<body class="ps ps-hub">' + header[0], 1).replace("<main>", '<main class="ps-hub">', 1)
    return page.replace("</body>", motion[0] + "\n</body>", 1)

# рубрики не про велнес — в страницы направлений не попадают (SESSIONS.md 26.09)
SKIP_RUBRICS = {"ИИ-автоматизация"}


def pick(arts, rubrics=(), include=(), exclude=()):
    out = []
    for r, slug, title, date in arts:
        if r in SKIP_RUBRICS or slug in exclude:
            continue
        if r in rubrics or any(k in slug for k in include):
            out.append((slug, html.unescape(title), date))
    return out


HUBS = [
    {
        "slug": "beremennost-i-rody",
        "title": "Беременность и роды: доула, подготовка и восстановление",
        "h1": "Беременность и роды",
        "kicker": "Замысел · беременность · роды · первые недели",
        "desc": "Подготовка к беременности, сопровождение доулы онлайн и в Кисловодске, подготовка к родам, восстановление и грудное вскармливание. Проверенный мастер и честные статьи.",
        "lead": "В это время особенно важно, кто рядом. Здесь доула, которую я знаю лично, и статьи журнала без запугивания и громких обещаний.",
        "c": "#35b6ff", "c2": "#d100ff",
        "services": [
            ("🌱", "Осознанная подготовка к беременности", "/podgotovka-k-beremennosti/", "Забота о теле, настрой и поддержка пары ещё до двух полосок."),
            ("🤍", "Сопровождение беременности онлайн", "/soprovozhdenie-beremennosti-onlayn/", "Доула на связи на всём сроке — из любого города."),
            ("🫶", "Подготовка к родам", "/podgotovka-k-rodam/", "Спокойствие, понимание процесса и план на день родов."),
            ("🌷", "Восстановление после родов", "/vosstanovlenie-posle-rodov/", "Бережная поддержка мамы в первые недели дома."),
            ("🍼", "Консультация по грудному вскармливанию", "/konsultaciya-grudnoe-vskarmlivanie/", "Практичная помощь с кормлением без давления."),
        ],
        "groups": [("Статьи журнала для будущих и молодых мам",
                    dict(rubrics=("Родителям",), exclude=("doula-smerti", "doula-kak-stat", "doula-kakoe-obrazovanie-nuzhno")))],
        "note": "Сопровождение доулы — немедицинская поддержка. Наблюдение беременности ведёт врач.",
    },
    {
        "slug": "telo-i-vosstanovlenie",
        "title": "Тело и восстановление: массаж на дому в Кисловодске",
        "h1": "Тело и восстановление",
        "kicker": "Тело · отдых · энергия",
        "desc": "Велнес-массаж с выездом на дом по Кисловодску и Кавминводам и понятные статьи о том, как восстановить силы после нагрузок, работы и стресса.",
        "lead": "Здесь мастер телесных практик, которому я доверяю, и простые способы вернуть силы после нагрузок, работы и стресса.",
        "c": "#9b6cff", "c2": "#00b4ff",
        "services": [
            ("🌿", "Аппаратный массаж на дому в Кисловодске", "/massage-kislovodsk/", "MARAFDY: выезд по Кавминводам, без масел, глубокое расслабление."),
        ],
        "groups": [
            ("Тело, СПА и санатории", dict(rubrics=("Тело и здоровье",))),
            ("Как восстановить силы", dict(include=("vosstan", "zhiznennaya-sila", "kak-pravilno-otdyhat", "otdyhayu-kak-den"))),
        ],
        "note": "Практики мастеров носят велнес-характер и не являются медицинской помощью. При жалобах на здоровье обратитесь к врачу.",
    },
    {
        "slug": "retrity-i-kmv",
        "title": "Ретриты и Кавминводы: уединение и места Кавказа",
        "h1": "Ретриты и Кавминводы",
        "kicker": "Дух · тишина · природа Кавказа",
        "desc": "Ретрит «Отшельник» у мастера Умаса под Железноводском, авторские экскурсии по Кисловодску и гид по горам, водопадам и тихим местам Кавказа.",
        "lead": "Когда тело в порядке, хочется глубины и тишины. Ретрит, который я знаю изнутри, авторские маршруты по Кисловодску и честный путеводитель по местам Кавказа.",
        "c": "#d100ff", "c2": "#00b4ff",
        "services": [
            ("🏔️", "Ретрит «Отшельник» у мастера Умаса", "/retrit-otshelnik/", "Мастер Умас принимает гостей на ретрите «Отшельник» под Железноводском: до пяти человек одновременно, тишина, жизнь на земле и разговоры о себе в группе и один на один. Это не отдых и не медицина."),
            ("🗺️", "Авторские экскурсии по Кисловодску", "/ekskursii-kislovodsk/", "Заповедные места, тайные тропы и легенды Кавминвод."),
        ],
        "groups": [
            ("Что такое ретрит и как выбрать", dict(include=("retrit",))),
            ("Кисловодск: что посмотреть", dict(include=("kislovod", "dom-rebrova", "dzhemagat"), exclude=("kislovodsk-massazh", "kislovodsk-sanatoriy-kakoy-luchshe", "spa-kislovodsk"))),
            ("Горы, водопады и тихие места Кавказа", dict(rubrics=("Осознанность и ретриты",))),
        ],
        "note": "Ретриты и экскурсии — велнес-формат, без медицинских услуг.",
    },
]


def plural(n):
    n10, n100 = n % 10, n % 100
    return "материал" if n10 == 1 and n100 != 11 else "материала" if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else "материалов"


def block(h, start, end):
    a = h.index(start)
    return h[a:h.index(end, a) + len(end)]



def icon_links(home):
    """Select actual head link tags, independent of their order and quoting.

    Preserve original tags. Collapse only semantically identical duplicates;
    absent icons/manifest or ambiguous attributes fail explicitly.
    """
    from html.parser import HTMLParser

    class HeadLinks(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.in_head = False
            self.template_depth = 0
            self.heads = 0
            self.closed = False
            self.links = []
            self.seen = set()
            self.has_icon = False
            self.manifest = None

        def handle_starttag(self, tag, attrs):
            if tag == "template":
                self.template_depth += 1
                return
            if self.template_depth:
                return
            if tag == "head":
                self.heads += 1
                self.in_head = True
                return
            if tag != "link" or not self.in_head:
                return
            rel_values = [value for key, value in attrs if key == "rel"]
            tokens = set(" ".join(value or "" for value in rel_values).lower().split())
            if not tokens.intersection(("icon", "apple-touch-icon", "manifest", "mask-icon")):
                return
            keys = [key for key, value in attrs]
            if len(keys) != len(set(keys)):
                raise ValueError("duplicate favicon link attribute")
            values = dict(attrs)
            href = values.get("href")
            if not href or not href.strip():
                raise ValueError("favicon link href missing")
            href = href.strip()
            if "manifest" in tokens:
                # Distinct existing manifest tags are retained, never arbitrarily
                # preferred. Only complete semantic duplicates collapse below.
                self.manifest = href
            if tokens.intersection(("icon", "apple-touch-icon", "mask-icon")):
                self.has_icon = True
            normalized = dict(values, rel=" ".join(sorted(tokens)), href=href)
            signature = tuple(sorted(normalized.items()))
            if signature not in self.seen:
                self.seen.add(signature)
                self.links.append(self.get_starttag_text())

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)

        def handle_endtag(self, tag):
            if tag == "template":
                self.template_depth = max(0, self.template_depth - 1)
                return
            if self.template_depth:
                return
            if tag == "head":
                self.in_head = False
                self.closed = True

    parser = HeadLinks()
    parser.feed(home)
    parser.close()
    if parser.heads != 1 or not parser.closed or not parser.has_icon or parser.manifest is None:
        raise ValueError("head favicon or manifest links missing")
    return "\n".join(parser.links)


def build():
    home = read("index.html")
    metrika = block(home, "<!-- Yandex.Metrika counter", "<!-- /Yandex.Metrika counter -->")
    icons = icon_links(home)
    tail = home[home.index("<!-- tl-consent-v2"):home.rindex("</body>")]
    podbor = block(home, "<!--tl-podbor-v1-->", "</section>")
    _footer = re.search(r'<footer\b[^>]*>.*?</footer>', home, re.S)
    if not _footer:raise ValueError("shared footer missing")
    footer = _footer.group(0)
    arts = articles()
    all_hubs = [(x["slug"], x["h1"]) for x in HUBS]

    for hub in HUBS:
        url = "%s/%s/" % (SITE, hub["slug"])
        used, groups = set(), []
        for name, rule in hub["groups"]:
            items = [a for a in pick(arts, **rule) if a[0] not in used]
            used.update(a[0] for a in items)
            if items:
                groups.append((name, items))
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "TimLabs", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": hub["h1"], "item": url}]},
            {"@type": "CollectionPage", "@id": url, "url": url, "name": hub["title"], "description": hub["desc"],
             "inLanguage": "ru", "isPartOf": {"@id": SITE + "/#site"}, "about": hub["h1"],
             "mainEntity": {"@type": "ItemList", "itemListElement": [
                 {"@type": "ListItem", "position": i + 1, "name": s[1], "url": SITE + s[2]} for i, s in enumerate(hub["services"])]}}]}
        cards = "\n".join(
            '      <article class="gcard rv" style="--c:{c};--c2:{c2}"><div class="g-top"><span class="g-ic" aria-hidden="true">{ic}</span>'
            '<span class="g-tag">{tag}</span></div><h3><a href="{u}">{t}</a></h3><p>{d}</p>'
            '<span class="g-more">Подробнее →</span></article>'.format(c=hub["c"], c2=hub["c2"], ic=ic, tag=html.escape(u.strip('/').replace('-',' ') and TAGS.get(u, 'Проверенный мастер')), t=html.escape(t), u=u, d=html.escape(d))
            for ic, t, u, d in hub["services"])
        lists = "\n".join(
            '    <h3 class="alist-h">%s</h3>\n    <ul class="alist">%s</ul>' % (html.escape(name), "".join(
                '<li><a href="/journal/%s/">%s<small>%s</small></a></li>' % (s, html.escape(t), d) for s, t, d in items))
            for name, items in groups)
        others = "".join('<a class="chip" href="/%s/">%s</a>' % (s, html.escape(n)) for s, n in all_hubs if s != hub["slug"])
        page = TEMPLATE.format(
            title=html.escape(hub["title"]), desc=html.escape(hub["desc"]), url=url,
            ld=json.dumps(ld, ensure_ascii=False, indent=1), metrika=metrika, icons=icons,
            h1=html.escape(hub["h1"]), kicker=html.escape(hub["kicker"]), lead=html.escape(hub["lead"]),
            cards=cards, podbor=podbor, lists=lists, others=others, note=html.escape(hub["note"]),
            footer=footer, tail=tail, n=sum(len(i) for _, i in groups), nw=plural(sum(len(i) for _, i in groups)))
        target = os.path.join(ROOT, hub["slug"], "index.html")
        previous = read(hub["slug"] + "/index.html") if os.path.isfile(target) else ""
        page = native_hub_page(page, previous, read("journal/index.html"))
        os.makedirs(os.path.join(ROOT, hub["slug"]), exist_ok=True)
        Path(os.path.join(ROOT, hub["slug"], "index.html")).write_text(page, encoding="utf-8")
        print(hub["slug"], "статей:", sum(len(i) for _, i in groups))


TAGS = {'/podgotovka-k-beremennosti/':'До беременности','/soprovozhdenie-beremennosti-onlayn/':'Во время беременности','/podgotovka-k-rodam/':'Перед родами','/vosstanovlenie-posle-rodov/':'После родов','/konsultaciya-grudnoe-vskarmlivanie/':'Кормление','/massage-kislovodsk/':'MARAFDY · выезд на дом','/retrit-otshelnik/':'Умас · ретрит','/transformacionnyj-retrit/':'Ретрит-центр','/ekskursii-kislovodsk/':'Прогулки по КМВ'}


TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} | TimLabs</title>
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
html{{scroll-behavior:smooth;background:#05070e}}
body{{margin:0;min-height:100vh;color:var(--text);font-family:var(--font-body);line-height:1.55;-webkit-font-smoothing:antialiased;overflow-x:hidden;
  background:radial-gradient(60% 50% at 15% 0%,rgba(0,180,255,.14),transparent 60%),radial-gradient(55% 50% at 90% 100%,rgba(209,0,255,.13),transparent 60%),linear-gradient(180deg,#05070e,#0a0f1c);background-attachment:fixed;background-color:#05070e}}
a{{color:inherit}}
main{{max-width:1080px;margin:0 auto;padding:clamp(22px,5vw,48px) 16px 60px}}
.crumb{{font-size:.8rem;color:var(--dim);margin-bottom:26px}}.crumb a{{color:var(--muted);text-decoration:none}}.crumb a:hover{{color:var(--cyan)}}
.hub-hero{{text-align:center;max-width:720px;margin:0 auto clamp(34px,6vw,56px)}}
.hub-hero h1{{font-family:var(--font-disp);font-size:clamp(2rem,6vw,3.1rem);line-height:1.08;margin:16px 0 14px;color:#fff;letter-spacing:-.015em;text-wrap:balance;
  background:linear-gradient(100deg,#fff 20%,var(--cyan) 60%,var(--magenta));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.hub-hero p{{color:var(--muted);font-size:1.05rem;margin:0 auto;max-width:58ch;text-wrap:pretty}}
.hub-cta{{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:22px}}
.btn{{display:inline-flex;align-items:center;gap:8px;padding:12px 22px;border-radius:13px;text-decoration:none;font-weight:700;font-size:.92rem;
  color:#00131f;background:linear-gradient(120deg,var(--cyan),#38c7ff);box-shadow:0 6px 24px rgba(0,180,255,.28);border:1px solid rgba(0,180,255,.55)}}
.btn.ghost{{background:rgba(14,20,36,.55);color:#fff;border-color:rgba(255,255,255,.14);box-shadow:none}}
.btn:focus-visible{{outline:2px solid #fff;outline-offset:3px}}
.note{{color:var(--dim);font-size:.8rem;text-align:center;margin:26px auto 0;max-width:60ch}}
footer{{max-width:760px;margin:40px auto 0;text-align:center;font-size:.7rem;color:var(--dim);line-height:1.6}}footer a{{color:var(--muted)}}
sup{{color:var(--magenta);font-weight:700}}
</style>
{metrika}
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="alternate" type="application/rss+xml" title="Журнал «Компас» — TimLabs" href="https://timlabs.online/rss.xml">
{icons}
</head>
<body>
<main>
  <nav class="crumb" aria-label="Хлебные крошки"><a href="/">ТимЛабс</a> → {h1}</nav>

  <header class="hub-hero">
    <span class="tlg-kicker">{kicker}</span>
    <h1>{h1}</h1>
    <p>{lead}</p>
    <div class="hub-cta"><a class="btn" href="#tl-podbor">Подобрать мастера за минуту</a><a class="btn ghost" href="#stati">Статьи по теме</a></div>
  </header>

  <section class="tlg-sec" aria-labelledby="m-h">
    <div class="tlg-head rv"><span class="tlg-kicker">Проверенные мастера</span><h2 id="m-h">С кем пройти этот путь</h2></div>
    <div class="tlg-grid">
{cards}
    </div>
  </section>

  <section class="tlg-sec" aria-label="Подбор мастера">
{podbor}
  </section>

  <section class="tlg-sec" id="stati" aria-labelledby="s-h">
    <div class="tlg-head rv"><span class="tlg-kicker">Журнал «Компас»</span><h2 id="s-h">Статьи по теме</h2><p>{n} {nw} простым языком, без запугивания и обещаний чудес.</p></div>
{lists}
    <p class="note">{note}</p>
  </section>

  <section class="tlg-sec" aria-label="Другие направления">
    <div class="gcard rv" style="text-align:center;align-items:center">
      <h2 style="font-family:var(--font-disp);color:#fff;margin:0;font-size:1.2rem">Другие направления</h2>
      <div class="chips" style="justify-content:center">{others}<a class="chip" href="/">На главную</a></div>
    </div>
  </section>

{footer}
</main>
{tail}</body>
</html>
"""

if __name__ == "__main__":
    build()
