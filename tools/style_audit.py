#!/usr/bin/env python3
"""Шаблонность журнала: что повторяется из статьи в статью (а не просто «машинные слова» внутри одной).
Запуск: python3 tools/style_audit.py [--json out.json] [--top 20]
Считает по всем /journal/*/:
  - дежурные сцены-зачины («Представьте…», «обычный вторник/вечер», «чашка кофе», «вы открываете глаза», «закрыли ноутбук»);
  - призывы-штампы («Попробуйте», «сделайте один шаг», «сегодня можно сделать»);
  - заголовки разделов и концовки, одинаковые в нескольких статьях;
  - одинаковый скелет (5 разделов + 5 вопросов), отсутствие голоса «я», монотонный ритм, короче 500 слов.
Выход: балл шаблонности на статью (0 — живая, 3+ — переписать), очередь худших, стоп-лист для humanize_ru.json (группа «дежурные сцены»).
Движок (локальная): вызывать перед публикацией как ворота — зачин, уже встречающийся в ≥3 статьях, не пропускать."""
import re, glob, html, json, sys, os, collections, statistics
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENES = [r"представьте", r"обычн(ый|ая|ое) (вторник|понедельник|вечер|утро|будничн)", r"чашк[аиуой]+ (кофе|чая)", r"вы (только что )?откр(ыли|ываете) глаза",
          r"закрыли ноутбук", r"вечер буднего дня", r"именно в этот момент", r"это не магия", r"тянетесь за телефоном"]
CALLS = [r"\bпопробуйте\b", r"сделайте (один|первый) шаг", r"сегодня(шний)? (можно сделать|шаг)", r"один практичн(ый|ого) шаг", r"начните с малого", r"вы начинаете (видеть|замечать|чувствовать)"]
ENDS = [r"смысл не в том,? чтобы", r"не в том,? чтобы .{3,40},? а в том,? чтобы", r"это не слабость,? а", r"главное — не"]

def text_of(path):
    s = open(path, encoding="utf-8").read()
    if 'http-equiv="refresh"' in s: return None
    body = s[s.find("<article>"):s.find("</article>")]
    heads = [html.unescape(re.sub("<[^>]+>", "", h)).strip().lower() for h in re.findall(r"<h2>(.*?)</h2>", body, re.S)]
    t = html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", "", body, flags=re.S))))
    return dict(text=t, heads=heads, nsec=len(heads), nfaq=s.count("<details>"))

def audit():
    arts = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "journal", "*", "index.html"))):
        d = text_of(f)
        if d: arts[f.split(os.sep)[-2]] = d
    head_cnt = collections.Counter(h for d in arts.values() for h in set(d["heads"]))
    scene_cnt = collections.Counter()
    for d in arts.values():
        for p in SCENES:
            if re.search(p, d["text"], re.I): scene_cnt[p] += 1
    rows = []
    for slug, d in arts.items():
        t = d["text"]; tl = t.lower(); why = []; score = 0.0
        for p in SCENES:
            if re.search(p, tl):
                k = scene_cnt[p]; score += 1.0 if k >= 3 else 0.4; why.append("сцена «%s» (в %d статьях)" % (p, k))
        for p in CALLS:
            n = len(re.findall(p, tl))
            if n: score += 0.3 * n; why.append("призыв «%s»×%d" % (p, n))
        for p in ENDS:
            if re.search(p, tl): score += 0.5; why.append("концовка-штамп «%s»" % p)
        rep = [h for h in d["heads"] if head_cnt[h] >= 3]
        if rep: score += 0.5 * len(rep); why.append("заголовки как у других: " + "; ".join(rep))
        if d["nsec"] == 5 and d["nfaq"] >= 5: score += 0.3; why.append("скелет 5+5")
        if not re.search(r"(^|[^а-яё])я ", tl): score += 0.7; why.append("нет «я»")
        sents = [x for x in re.split(r"(?<=[.!?…])\s+", t) if len(x.split()) > 1]
        L = [len(x.split()) for x in sents]
        cv = statistics.pstdev(L) / statistics.mean(L) if L else 0
        if cv < 0.38: score += 0.5; why.append("ровный ритм (CV %.2f)" % cv)
        words = len(re.findall(r"[а-яёА-ЯЁ]+", t))
        if words < 500: score += 0.5; why.append("коротко (%d слов)" % words)
        rows.append(dict(slug=slug, score=round(score, 2), words=words, why=why))
    rows.sort(key=lambda r: -r["score"])
    stop = {"dezhurnye_sceny": [p for p, k in scene_cnt.items() if k >= 2]}
    return rows, scene_cnt, head_cnt, stop

if __name__ == "__main__":
    rows, scene_cnt, head_cnt, stop = audit()
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 20
    print("статей:", len(rows), "| балл ≥3 (переписать):", sum(1 for r in rows if r["score"] >= 3), "| 1.5–3 (подправить):", sum(1 for r in rows if 1.5 <= r["score"] < 3))
    print("\nДежурные сцены (в скольких статьях):"); [print(" ", k, p) for p, k in scene_cnt.most_common() if k]
    print("\nЗаголовки разделов, повторяющиеся в ≥3 статьях:"); [print(" ", k, h) for h, k in head_cnt.most_common() if k >= 3]
    print("\nОчередь переписчику (худшие первыми):")
    for r in rows[:top]: print(" %4.1f  %-45s %s" % (r["score"], r["slug"], "; ".join(r["why"])[:140]))
    if "--json" in sys.argv:
        json.dump(dict(queue=rows, scenes=dict(scene_cnt), heads={h: k for h, k in head_cnt.items() if k >= 2}, stoplist=stop), open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
