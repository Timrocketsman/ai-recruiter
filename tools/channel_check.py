#!/usr/bin/env python3
"""Контроль канала @timlabs_journal: анонсы должны совпадать со статьями на сайте.

    python3 tools/channel_check.py            # посты из https://t.me/s/timlabs_journal, статьи из репозитория
    python3 tools/channel_check.py --live     # заголовки статей брать с timlabs.online, не из файлов
    python3 tools/channel_check.py --file x.html   # разбор сохранённой страницы канала (без сети)
    python3 tools/channel_check.py --json     # машинный вывод
    python3 tools/channel_check.py --deep 8   # весь архив: ещё 8 страниц по 20 постов назад (19.10: в архиве было 74 расхождения)

Что проверяет по каждому посту со ссылкой на /journal/…:
  1. первая строка поста (заголовок анонса) совпадает с H1 статьи — иначе «старый анонс»
     (статью переписали, пост остался; дистрибьютор должен править пост, не оставлять);
  2. статья существует, не снята и не перенесена (redirect/canonical на другой адрес);
  3. в заголовке нет тавтологии «N полезных/простых привычек/правил/способов…» подряд с другими
     постами одной формы (слово Тима 13.10: «одна тема — одна статья», «убери тавтологию»);
  4. текст поста без дежурных сцен (слово Тима 11.10).
Код выхода 1, если есть замечания, — удобно для supervise/ежедневного отчёта.
Только чтение: ничего не правит и никуда не пишет.
"""
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://timlabs.online"
CHANNEL = "https://t.me/s/timlabs_journal"
# «N полезных привычек», «3 простых правила», «2 простых способа» и т.п.
TAUTOLOGY = re.compile(r"^\s*(\d+|одн[аоу]|две|три|четыре|пять)\s+(полезн\w*|прост\w*|главн\w*|лучш\w*)\s+"
                       r"(привыч\w*|правил\w*|способ\w*|шаг\w*|совет\w*)", re.I)
STOCK = ["представь", "представьте", "обычный вторник", "обычный вечер", "чашк", "закрыли ноутбук",
         "попробуйте", "смысл не в том", "главное — не", "главное - не"]


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (timlabs channel_check)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def norm(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace(" ", " ").replace("ё", "е").replace("Ё", "Е")
    s = re.sub(r"[«»\"'“”„]", "", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s.rstrip(".!?:;,")


def parse_channel(page):
    posts = []
    for m in re.findall(r'<div class="tgme_widget_message_wrap.*?(?=<div class="tgme_widget_message_wrap|$)', page, re.S):
        t = re.search(r'<time datetime="([^"]+)"', m)
        link = re.search(r'data-post="([^"]+)"', m)
        txt = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', m, re.S)
        body = re.sub(r"<br\s*/?>", "\n", txt.group(1)) if txt else ""
        body = html.unescape(re.sub(r"<[^>]+>", "", body))
        urls = [u for u in re.findall(r'href="(https://timlabs\.online/[^"#?]*)"', m) if "/journal/" in u]
        first = next((ln.strip() for ln in body.split("\n") if ln.strip()), "")
        posts.append({"when": t.group(1) if t else "", "post": link.group(1) if link else "",
                      "title": first, "text": body, "urls": sorted(set(urls))})
    return posts


def article_h1(url, live):
    """→ (h1, статус) где статус: ok | missing | moved:<адрес> | removed."""
    path = url[len(SITE):]
    if live:
        try:
            h = fetch(url)
        except Exception as e:
            return "", "missing" if "404" in str(e) else "error:%s" % e
    else:
        p = os.path.join(ROOT, path.strip("/"), "index.html")
        if not os.path.exists(p):
            return "", "missing"
        h = open(p, encoding="utf-8").read()
    if re.search(r"<title>(Материал перенесён|Страница удалена)", h):
        return "", "removed"
    if 'http-equiv="refresh"' in h:
        to = re.search(r'url=([^"\']+)', h)
        return "", "moved:" + (to.group(1) if to else "?")
    c = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    if c and c.group(1).rstrip("/") != url.rstrip("/"):
        return "", "moved:" + c.group(1)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    return (html.unescape(re.sub(r"<[^>]+>", "", h1.group(1))).strip() if h1 else ""), "ok"


def check(posts, live=False):
    out, forms = [], {}
    for p in posts:
        if not p["urls"]:
            continue
        notes = []
        for u in p["urls"]:
            h1, st = article_h1(u, live)
            if st != "ok":
                notes.append("статья %s: %s" % (u, st))
                continue
            if p["title"] and norm(p["title"]) != norm(h1):
                notes.append("старый анонс: в посте «%s», на сайте «%s»" % (p["title"], h1))
            if TAUTOLOGY.match(h1):
                notes.append("тавтология в заголовке статьи: «%s»" % h1)
        mt = TAUTOLOGY.match(p["title"] or "")
        if mt:
            key = mt.group(3)[:5].lower()
            forms.setdefault(key, []).append(p["post"])
            notes.append("тавтология в анонсе: «%s»" % p["title"])
        low = norm(p["text"])
        for s in STOCK:
            if s in low:
                notes.append("дежурная сцена в анонсе: «%s»" % s)
                break
        if notes:
            out.append({"when": p["when"], "post": p["post"], "urls": p["urls"], "notes": notes})
    for key, ps in forms.items():
        if len(ps) > 1:
            out.append({"when": "", "post": ",".join(ps), "urls": [],
                        "notes": ["одна форма заголовка «N … %s…» в %d постах — одна тема, одна статья" % (key, len(ps))]})
    return out


def main():
    a = sys.argv[1:]
    live = "--live" in a
    if "--file" in a:
        page = open(a[a.index("--file") + 1], encoding="utf-8").read()
    else:
        page = fetch(CHANNEL)
        if "--deep" in a:
            pages = int(a[a.index("--deep") + 1])
            for _ in range(pages):
                ids = [int(x) for x in re.findall(r'data-post="[^"/]+/(\d+)"', page)]
                if not ids:
                    break
                older = fetch(CHANNEL + "?before=%d" % min(ids))
                if not re.search(r'data-post="', older):
                    break
                page = older + page
    posts = parse_channel(page)
    seen, uniq = set(), []
    for p_ in posts:
        if p_["post"] and p_["post"] in seen:
            continue
        seen.add(p_["post"]); uniq.append(p_)
    posts = uniq
    problems = check(posts, live)
    if "--json" in a:
        print(json.dumps({"posts": len(posts), "problems": problems}, ensure_ascii=False, indent=1))
    else:
        print("Постов на странице канала: %d, с ссылками на журнал: %d" % (len(posts), sum(1 for p in posts if p["urls"])))
        for pr in problems:
            print("- %s %s %s" % (pr["when"][:16], pr["post"], " ".join(pr["urls"])))
            for n in pr["notes"]:
                print("    " + n)
        print("Замечаний: %d" % len(problems) if problems else "Канал совпадает с сайтом: замечаний нет")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
