#!/usr/bin/env python3
"""Ворота тем и заголовков журнала «Компас» (правила Тима 13.10 и 14.10). Только stdlib.

Две проверки, одна логика для сайта (pre-commit `monetize_patch.headline_gate`) и для движка (`journalist`):

  headline_ok(h1) -> (bool, причина)
      Запрещён заголовок-штамп «N полезных/простых/главных/лучших привычек|правил|способов|шагов|советов…»
      (3, 2, 1, 10, «одна», «две», «три»…). Слово Тима 13.10: «убери тавтологию и запрети так делать вообще».

  same_topic(query, existing) -> slug | None
      `existing` — {slug: заголовок} (или список пар). Запрос «10 полезных привычек» или «способности саморазвития»
      считается ТОЙ ЖЕ темой, что уже вышедшая статья, если после отбрасывания числительных и служебных слов
      основы слов совпадают на ≥60 % (по меньшему набору) и совпали ≥2 основы. Правило «одна тема — одна статья»:
      тогда статью не писать, а дописать существующую (`update`).

Подключение в движке (локальная сессия, /seo_agents):
  from site.tools import topic_gate            # /seo_agents/site — клон репозитория сайта
  dup = topic_gate.same_topic(query, {a["slug"]: a["title"] for a in journal_index})
  if dup: -> rewriter.update(dup) вместо новой статьи
  ok, why = topic_gate.headline_ok(h1)          # перед публикацией; не ok -> переписать заголовок, не публиковать

CLI:  python3 tools/topic_gate.py selftest
      python3 tools/topic_gate.py check "10 полезных привычек"      # против статей репозитория
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NUM = r"(?:\d+|одн[аоуи]\w*|дв[аеух]\w*|тр[иёе]\w*|четыр\w*|пят\w*|шест\w*|сем\w*|восем\w*|девят\w*|десят\w*)"
TEMPLATE = re.compile(r"^\s*" + NUM + r"\s+(полезн\w*|прост\w*|главн\w*|лучш\w*|важн\w*|эффективн\w*)\s+"
                      r"(привыч\w*|правил\w*|способ\w*|шаг\w*|совет\w*|приём\w*|прием\w*|лайфхак\w*)", re.I)
TEMPLATE2 = re.compile(r"^\s*" + NUM + r"\s+(привыч\w*|правил\w*|способ\w*|шаг\w*|совет\w*)\b", re.I)

STOP = set("""и в во на не что как это для от по с со к у о об из за до при без над под про же бы ли или
а но да то все всё свой свои своя своё ваш ваша ваше ваши их его её мой моя моё мои наш наша наше наши
который которая которое которые чтобы если когда где кто чем чему такой такая такое такие самый сама сам само
реально просто можно нужно надо стоит каждый каждая каждое день года год лет неделю неделя месяц
полезный полезные полезных полезная полезную простой простые простых главный главные лучший лучшие
один одна одно одну одной два две три четыре пять шесть семь восемь девять десять""".split())

ENDINGS = ("иями", "ями", "ами", "ого", "его", "ому", "ему", "ыми", "ими", "ешь", "ить", "ать", "ять", "уть",
           "ой", "ей", "ий", "ый", "ая", "яя", "ое", "ее", "ые", "ие", "ую", "юю", "ов", "ев", "ам", "ям", "ах", "ях",
           "ом", "ем", "ью", "ия", "ие", "ий", "ы", "и", "а", "я", "о", "е", "у", "ю", "ь", "й")


def stem(w):
    w = w.lower().replace("ё", "е")
    for e in ENDINGS:
        if len(w) - len(e) >= 4 and w.endswith(e):
            w = w[: -len(e)]
            break
    return w[:7]  # грубая основа: «саморазвитие/саморазвитию» → «саморазв»


def stems(text):
    words = re.findall(r"[а-яёА-ЯЁa-zA-Z]+", text or "")
    out = set()
    for w in words:
        lw = w.lower().replace("ё", "е")
        if lw in STOP or len(lw) < 3 or re.fullmatch(r"\d+", lw):
            continue
        out.add(stem(lw))
    return out


def headline_ok(h1):
    h = (h1 or "").strip()
    if TEMPLATE.match(h):
        return False, "заголовок-штамп «N полезных/простых …» (запрет Тима 13.10)"
    if TEMPLATE2.match(h):
        return False, "заголовок-штамп «N привычек/правил/способов …» (запрет Тима 13.10)"
    return True, ""


def same_topic(query, existing, threshold=0.6, min_common=2):
    """→ slug существующей статьи той же темы или None."""
    q = stems(query)
    if not q:
        return None
    min_common = min(min_common, len(q))  # запрос из одного слова («ретрит») — одна тема, если слово совпало
    items = existing.items() if isinstance(existing, dict) else existing
    best, best_score = None, 0.0
    for slug, title in items:
        t = stems(title)
        if not t:
            continue
        common = q & t
        score = len(common) / max(1, min(len(q), len(t)))
        if len(common) >= min_common and score >= threshold and score > best_score:
            best, best_score = slug, score
    return best


def site_titles():
    """{slug: H1} по статьям репозитория (живые, не перенесённые)."""
    out = {}
    jd = os.path.join(ROOT, "journal")
    for slug in sorted(os.listdir(jd)):
        f = os.path.join(jd, slug, "index.html")
        if not os.path.isfile(f):
            continue
        h = open(f, encoding="utf-8").read()
        if 'http-equiv="refresh"' in h:
            continue
        m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        if m:
            out[slug] = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return out


def selftest():
    bad = ["3 полезные привычки: что реально работает", "10 полезных привычек: как выбрать", "Одна полезная привычка: с чего начать",
           "2 простых правила сна", "Три главных способа отдохнуть", "5 шагов к цели"]
    good = ["Привычки, которые держатся: что реально работает каждый день", "С чего начать: одна привычка вместо десяти",
            "Связка привычек: как закрепить две за неделю без силы воли", "Ретрит: что это такое", "Пять недель работы и неделя отдыха: как устроен цикл 5/1"]
    for h in bad:
        assert not headline_ok(h)[0], h
    for h in good:
        assert headline_ok(h)[0], h
    ex = {"1-poleznuyu-privychku": "С чего начать: одна привычка вместо десяти", "retrit": "Что такое ретрит простыми словами",
          "sposobnosti-samorazvitiya": "Способности к саморазвитию: какие они бывают", "gora-cheget": "Гора Чегет: как устроена поездка"}
    assert same_topic("саморазвитие способностей", ex) == "sposobnosti-samorazvitiya"
    assert same_topic("способности саморазвития", ex) == "sposobnosti-samorazvitiya"
    assert same_topic("что такое ретрит", ex) == "retrit"
    assert same_topic("гора Эльбрус как добраться", ex) is None
    titles = site_titles()
    hit = same_topic("10 полезных привычек", titles)
    assert hit and "privych" in hit, hit
    bad_live = [(s, t) for s, t in titles.items() if not headline_ok(t)[0]]
    print("selftest ok; статей:", len(titles), "; штампов в живых заголовках:", len(bad_live), bad_live[:5])
    return 0


def main():
    a = sys.argv[1:]
    if not a or a[0] == "selftest":
        return selftest()
    if a[0] == "check" and len(a) > 1:
        q = " ".join(a[1:])
        ok, why = headline_ok(q)
        dup = same_topic(q, site_titles())
        print(json.dumps({"query": q, "headline_ok": ok, "why": why, "same_topic": dup}, ensure_ascii=False))
        return 0 if ok and not dup else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
