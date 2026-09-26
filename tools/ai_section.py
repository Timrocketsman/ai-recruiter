#!/usr/bin/env python3
"""Раздел «Мои услуги: ИИ-автоматизация» + баннер «Журнал под ключ» на главной.

Вставляется ТОЛЬКО когда страница /ii-avtomatizaciya/ уже есть в репозитории
(иначе ссылки вели бы на 404). Идемпотентно: блок между метками tl-ai-v1 заменяется целиком.
  python3 tools/ai_section.py            # вставить/обновить, если страница есть
  python3 tools/ai_section.py --preview  # вставить в любом случае (для проверки глазами)
Цен здесь нет: цены только на /ii-avtomatizaciya/ (решение Тима 26.09, SESSIONS.md).
Якоря и тексты услуг — от локальной сессии «TimLabs офис» (SESSIONS.md, 26.09).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "/ii-avtomatizaciya/"
BOT = "https://t.me/TimLabs_bot?start=ai"
START, END = "<!--tl-ai-v1-->", "<!--/tl-ai-v1-->"
ANCHOR = "  <!-- ============ МОИ ПРОЕКТЫ ============ -->"


def plural(n, one, few, many):
    n10, n100 = n % 10, n % 100
    return one if n10 == 1 and n100 != 11 else few if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else many


def count_articles():
    t = open(os.path.join(ROOT, "journal/index.html"), encoding="utf-8").read()
    return len(re.findall(r'<article class="card"', t))


SERVICES = [
    ("🙋", "Частным лицам", "Автоматизация рутины", "Разберу вашу рутину и настрою ИИ-помощников под почту, записи, учёбу и личные проекты.", "chastnym", "#35b6ff", "#00b4ff"),
    ("🏢", "Бизнесу", "ИИ для бизнеса: боты и агенты", "Ответы клиентам и заявки, отчёты и документы, ИИ-агенты на данных компании.", "biznesu", "#00b4ff", "#d100ff"),
    ("🌐", "Бренду и эксперту", "Экосистема цифрового следа", "Сайт, журнал, соцсети и ролики — и видимость в поиске и в ИИ-ассистентах.", "cifrovoj-sled", "#d100ff", "#35b6ff"),
]


def block(n):
    cards = "\n".join(
        '      <article class="gcard rv" style="--c:{c};--c2:{c2}"><div class="g-top"><span class="g-ic" aria-hidden="true">{ic}</span>'
        '<span class="g-tag">{tag}</span></div><h3><a href="{p}#{a}">{t}</a></h3><p>{d}</p><span class="g-more">Подробнее →</span></article>'
        .format(ic=ic, tag=tag, t=t, d=d, p=PAGE, a=a, c=c, c2=c2) for ic, tag, t, d, a, c, c2 in SERVICES)
    return """{S}
<style>
.b2b{{--c:#00b4ff;--c2:#d100ff;position:relative;isolation:isolate;overflow:hidden;border-radius:26px;margin-bottom:16px;
  display:grid;grid-template-columns:1.25fr .75fr;gap:clamp(18px,4vw,40px);align-items:center;padding:clamp(24px,4vw,40px);
  background:radial-gradient(120% 140% at 0% 0%,rgba(0,180,255,.16),transparent 55%),radial-gradient(120% 140% at 100% 100%,rgba(209,0,255,.16),transparent 55%),rgba(12,17,32,.55);
  border:1px solid rgba(255,255,255,.1);box-shadow:inset 0 1px 0 rgba(255,255,255,.14),0 20px 60px rgba(0,0,0,.4)}}
@supports (backdrop-filter:blur(1px)){{.b2b{{backdrop-filter:blur(14px) saturate(140%);-webkit-backdrop-filter:blur(14px) saturate(140%)}}}}
/* медленно бегущая световая рамка — заметно, но не мигает */
.b2b::before{{content:"";position:absolute;inset:-1px;border-radius:inherit;padding:1.5px;z-index:-1;pointer-events:none;
  background:conic-gradient(from var(--a,0deg),transparent 0 60%,var(--c) 75%,var(--c2) 85%,transparent 95%);
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;
  animation:b2bspin 9s linear infinite}}
@property --a{{syntax:"<angle>";inherits:false;initial-value:0deg}}
@keyframes b2bspin{{to{{--a:360deg}}}}
.b2b .k{{display:inline-flex;gap:8px;align-items:center;font-size:.68rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:#ffd166}}
.b2b .k i{{width:7px;height:7px;border-radius:50%;background:#ffd166;box-shadow:0 0 10px #ffd166}}
.b2b h2{{font-family:var(--font-disp);font-size:clamp(1.45rem,3.6vw,2.1rem);line-height:1.12;margin:12px 0 10px;color:#fff;text-wrap:balance;letter-spacing:-.01em}}
.b2b h2 span{{background:linear-gradient(100deg,var(--c),var(--c2));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.b2b p{{margin:0 0 14px;color:var(--muted);font-size:.98rem;line-height:1.6;max-width:52ch}}
.b2b ul{{list-style:none;padding:0;margin:0 0 20px;display:grid;gap:8px}}
.b2b li{{display:flex;gap:10px;color:var(--text);font-size:.92rem}}
.b2b li::before{{content:"✓";color:var(--c);font-weight:800}}
.b2b .cta{{display:flex;flex-wrap:wrap;gap:10px}}
.b2b .cta a{{display:inline-flex;align-items:center;gap:8px;padding:13px 22px;border-radius:13px;font-weight:800;font-size:.92rem;text-decoration:none}}
.b2b .cta .p{{color:#00131f;background:linear-gradient(120deg,var(--c),#38c7ff);box-shadow:0 8px 28px rgba(0,180,255,.35)}}
.b2b .cta .s{{color:#fff;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.04)}}
.b2b .cta a:hover{{transform:translateY(-2px)}}.b2b .cta a:focus-visible{{outline:2px solid #fff;outline-offset:3px}}
/* правая часть: стопка «статей» — показывает продукт, а не обещания */
.b2b .vis{{position:relative;height:220px}}
.b2b .sheet{{position:absolute;left:8%;right:8%;padding:14px 16px;border-radius:14px;background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.12);box-shadow:0 10px 30px rgba(0,0,0,.35);backdrop-filter:blur(6px)}}
.b2b .sheet b{{display:block;height:9px;border-radius:5px;background:linear-gradient(90deg,rgba(255,255,255,.55),rgba(255,255,255,.15));margin-bottom:8px}}
.b2b .sheet s{{display:block;height:6px;border-radius:4px;background:rgba(255,255,255,.12);margin-top:6px;text-decoration:none}}
.b2b .s1{{top:0;transform:rotate(-4deg);opacity:.55}}.b2b .s2{{top:34px;transform:rotate(2deg);opacity:.8}}
.b2b .s3{{top:70px;animation:b2bfloat 6s ease-in-out infinite}}
@keyframes b2bfloat{{50%{{transform:translateY(-6px)}}}}
.b2b .num{{position:absolute;right:4%;bottom:0;padding:10px 14px;border-radius:14px;text-align:right;
  background:rgba(5,7,14,.7);border:1px solid rgba(0,180,255,.35)}}
.b2b .num strong{{display:block;font-family:var(--font-disp);font-size:1.7rem;color:#fff;line-height:1}}
.b2b .num small{{font-size:.72rem;color:var(--muted)}}
@media (max-width:760px){{.b2b{{grid-template-columns:1fr}}.b2b .vis{{height:170px;order:-1}}}}
@media (prefers-reduced-motion:reduce){{.b2b::before,.b2b .s3{{animation:none}}}}
</style>
  <section class="tlg-sec" id="uslugi" aria-labelledby="uslugi-h">
    <div class="tlg-head rv">
      <span class="tlg-kicker">Мои услуги</span>
      <h2 id="uslugi-h">ИИ-автоматизация — моя собственная работа</h2>
      <p>Эту работу я делаю сам: строю ИИ-агентов и автоматизацию, на которой работает и этот сайт.</p>
    </div>
    <article class="b2b rv" aria-labelledby="b2b-h">
      <div>
        <span class="k"><i aria-hidden="true"></i>Для бизнеса и экспертов</span>
        <h2 id="b2b-h">Журнал под ключ: <span>статьи, по которым вас находят в поиске</span></h2>
        <p>Офис ИИ-агентов пишет статьи по реальному поисковому спросу, публикует их и следит за качеством. Вы получаете живой экспертный журнал без штата авторов.</p>
        <ul>
          <li>Уже работает здесь: журнал «Компас» — {N} {W}</li>
          <li>Тексты проверяются на «машинность» и чужие ссылки</li>
          <li>Анонсы — в Telegram, Дзен и ВКонтакте</li>
        </ul>
        <div class="cta">
          <a class="p" href="{P}#zhurnal-pod-klyuch">Подробнее и стоимость</a>
          <a class="s" href="{B}" target="_blank" rel="noopener">Обсудить в боте</a>
        </div>
      </div>
      <div class="vis" aria-hidden="true">
        <div class="sheet s1"><b></b><s></s><s></s></div>
        <div class="sheet s2"><b></b><s></s><s></s></div>
        <div class="sheet s3"><b></b><s></s><s></s><s></s></div>
        <div class="num"><strong>{N}</strong><small>{W} в «Компасе»</small></div>
      </div>
    </article>
    <div class="tlg-grid">
{cards}
    </div>
  </section>
<script>/* цель b2b_click (Метрика id 664071713) — только после согласия */
document.getElementById('uslugi').addEventListener('click',function(e){{var a=e.target.closest&&e.target.closest('a[href^="/ii-avtomatizaciya/"],a[href*="start=ai"]');
if(a)try{{if(typeof ym==='function')ym(111725024,'reachGoal','b2b_click',{{from:location.pathname}});}}catch(_){{}}}});</script>
{E}
""".format(S=START, E=END, N=n, W=plural(n, "статья", "статьи", "статей"), P=PAGE, B=BOT, cards=cards)


AS, AE = "<!--tl-ai-articles-v1-->", "<!--/tl-ai-articles-v1-->"


def ai_articles():
    """Автосписок статей рубрики «ИИ-автоматизация» на /ii-avtomatizaciya/ (перед подвалом)."""
    p = os.path.join(ROOT, PAGE.strip("/"), "index.html")
    if not os.path.exists(p):
        return
    t = open(os.path.join(ROOT, "journal/index.html"), encoding="utf-8").read()
    items = re.findall(r'data-rubric="ИИ-автоматизация"><a class="card-link" href="https://timlabs\.online(/journal/[^"]+)"><h2 class="card-title">([^<]*)</h2>', t)
    h = open(p, encoding="utf-8").read()
    old = re.search(re.escape(AS) + ".*?" + re.escape(AE) + "\n?", h, re.S)
    if not items:
        new_h = h.replace(old.group(0), "") if old else h
    else:
        li = "".join('<li><a href="%s">%s</a></li>' % (u, t_) for u, t_ in items[:12])
        blk = (AS + '<section class="tl-ai-art" aria-labelledby="tl-ai-art-h"><style>'
               '.tl-ai-art{max-width:900px;margin:40px auto;padding:0 16px}.tl-ai-art h2{margin:0 0 14px}'
               '.tl-ai-art ul{list-style:none;padding:0;margin:0;display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(min(100%,280px),1fr))}'
               '.tl-ai-art a{display:block;height:100%;padding:14px 16px;border-radius:14px;text-decoration:none;color:inherit;'
               'background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1)}.tl-ai-art a:hover{border-color:rgba(0,180,255,.5)}'
               '</style><h2 id="tl-ai-art-h">Статьи рубрики «ИИ-автоматизация»</h2><ul>' + li + '</ul>'
               '<p><a href="/journal/">Весь журнал «Компас» →</a></p></section>' + AE + "\n")
        new_h = h.replace(old.group(0), blk) if old else h.replace("<footer", blk + "<footer", 1)
    if new_h != h:
        open(p, "w", encoding="utf-8").write(new_h)
        print("статьи рубрики на странице услуг:", len(items))


def main():
    ai_articles()
    preview = "--preview" in sys.argv
    p = os.path.join(ROOT, "index.html")
    h = open(p, encoding="utf-8").read()
    has_page = os.path.exists(os.path.join(ROOT, PAGE.strip("/"), "index.html"))
    if not has_page and not preview:
        # страницы нет — блок не показываем (и убираем, если остался)
        h2 = re.sub(re.escape(START) + ".*?" + re.escape(END) + "\n?", "", h, flags=re.S)
        if h2 != h:
            open(p, "w", encoding="utf-8").write(h2)
        print("страницы %s нет — раздел не вставлен" % PAGE)
        return
    new = block(count_articles())
    if START in h:
        h2 = re.sub(re.escape(START) + ".*?" + re.escape(END) + "\n?", lambda m: new, h, count=1, flags=re.S)
    else:
        h2 = h.replace(ANCHOR, new + "\n" + ANCHOR, 1)
    if h2 != h:
        open(p, "w", encoding="utf-8").write(h2)
    print("раздел вставлен" + (" (предпросмотр)" if preview and not has_page else ""))


if __name__ == "__main__":
    main()
