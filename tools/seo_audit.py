#!/usr/bin/env python3
"""SEO-проверка всех страниц timlabs.online (только чтение).  python3 tools/seo_audit.py [--all]

Проверяет: title (длина, дубли), description (длина, дубли), один h1, canonical = адрес страницы,
lang, og:title/description/image, JSON-LD разбирается, alt у картинок, страница в sitemap,
внутренние ссылки ведут на существующие страницы, noindex, порядок заголовков (h1→h2→h3).
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://timlabs.online"
SKIP = {".git", "tools", "assets", "media", "scripts", "data"}


def pages():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP]
        if "index.html" in fns:
            rel = os.path.relpath(dp, ROOT)
            yield ("/" if rel == "." else "/" + rel + "/"), os.path.join(dp, "index.html")


def text(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def main():
    sitemap = set(re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()))
    issues = collections.defaultdict(list)
    titles, descs = collections.defaultdict(list), collections.defaultdict(list)
    exist = {u for u, _ in pages()}
    for url, p in pages():
        h = open(p, encoding="utf-8").read()
        if re.search(r"<title>(Материал перенесён|Страница удалена)", h) or 'http-equiv="refresh"' in h:
            continue
        body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S)
        add = lambda m: issues[url].append(m)
        noindex = re.search(r'name="robots"[^>]*noindex', h)
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        t = text(t.group(1)) if t else ""
        if not t: add("нет title")
        elif not 25 <= len(t) <= 70: add("title %d симв." % len(t))
        titles[t].append(url)
        d = re.search(r'<meta name="description" content="([^"]*)"', h)
        d = d.group(1) if d else ""
        if not d: add("нет description")
        elif not 70 <= len(d) <= 170: add("description %d симв." % len(d))
        descs[d].append(url)
        h1 = re.findall(r"<h1[\s>]", body)
        if len(h1) != 1: add("h1: %d" % len(h1))
        c = re.search(r'<link rel="canonical" href="([^"]+)"', h)
        if not c: add("нет canonical")
        elif c.group(1) != SITE + url and url != "/404.html": add("canonical ≠ адрес: " + c.group(1))
        if '<html lang="ru"' not in h: add("нет lang=ru")
        for og in ("og:title", "og:description", "og:image"):
            if 'property="%s"' % og not in h: add("нет " + og)
        for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try: json.loads(m)
            except Exception as e: add("JSON-LD не разбирается: %s" % e)
        for img in re.findall(r"<img\b[^>]*>", body):
            if "alt=" not in img: add("img без alt")
        if not noindex and url != "/404.html" and SITE + url not in sitemap: add("нет в sitemap")
        if noindex and SITE + url in sitemap: add("noindex, но в sitemap")
        levels = [int(x) for x in re.findall(r"<h([1-6])[\s>]", body)]
        for a, b in zip(levels, levels[1:]):
            if b > a + 1: add("скачок заголовков h%d→h%d" % (a, b)); break
        for href in set(re.findall(r'href="(?:https://timlabs\.online)?(/[^"#?]*)', body)):
            if href.endswith("/") and href not in exist and not href.startswith("/assets"):
                add("битая ссылка " + href)
    for t, us in titles.items():
        if t and len(us) > 1:
            for u in us: issues[u].append("title-дубль с %d стр." % (len(us) - 1))
    for d, us in descs.items():
        if d and len(us) > 1:
            for u in us: issues[u].append("description-дубль")
    for loc in sorted(sitemap):
        u = loc.replace(SITE, "")
        if u.endswith("/") and u not in exist: issues[u].append("в sitemap, но страницы нет")
    total = collections.Counter(m.split(":")[0].split(" ")[0] + " " + " ".join(m.split(" ")[1:2]) for v in issues.values() for m in v)
    only = None if "--all" in sys.argv else (lambda u: not u.startswith("/journal/") or u == "/journal/")
    for u in sorted(issues):
        if only is None or only(u):
            print(u, "|", "; ".join(issues[u]))
    print("\nВсего по типам:", dict(total.most_common()))


if __name__ == "__main__":
    main()
