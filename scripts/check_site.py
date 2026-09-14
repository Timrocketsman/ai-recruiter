#!/usr/bin/env python3
"""Проверка целостности статического сайта timlabs.online.

Только стандартная библиотека — работает одинаково на маке и в веб-сессии,
ставить ничего не нужно.

Что проверяется:
  * у каждой страницы есть title, description, canonical, og:*, ровно один <h1>;
  * canonical и og:url совпадают с реальным путём страницы;
  * sitemap.xml валиден, без дублей, все <loc> существуют;
  * каждая статья журнала присутствует в sitemap.xml;
  * rss.xml валиден, ссылки items существуют, guid совпадает с link;
  * внутренние ссылки и картинки (href="/…", src="/…") ведут на существующие файлы.

Использование:
    python3 scripts/check_site.py                      # весь сайт
    python3 scripts/check_site.py journal/gora-elbrus  # только эти страницы
    python3 scripts/check_site.py --quiet              # только проблемы
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from fnmatch import fnmatch
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://timlabs.online"

# Каталоги, которые не являются страницами сайта.
SKIP_DIRS = {".git", ".github", ".claude", "scripts", "assets", "media", "node_modules"}

# Файлы-подтверждения прав для поисковиков и Дзена — это не страницы.
SKIP_FILES = ("zen_*.html", "google*.html", "yandex_*.html")

REQUIRED_META = ("description", "og:title", "og:description", "og:url")

# Незаменённые плейсхолдеры шаблона, уехавшие в прод.
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_][A-Z0-9_]*\}\}")


class Page(HTMLParser):
    """Вытаскивает из страницы head-метаданные, заголовки и все ссылки."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.title: str = ""
        self.meta: dict[str, str] = {}
        self.canonical: str | None = None
        self.h1_count = 0
        self.refs: list[str] = []
        self.refresh_to: str | None = None
        self._in_title = False
        self._in_h1 = False

    @property
    def noindex(self) -> bool:
        return "noindex" in self.meta.get("robots", "").lower()

    @property
    def is_redirect(self) -> bool:
        return self.refresh_to is not None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
            self.h1_count += 1
        elif tag == "meta":
            if a.get("http-equiv", "").lower() == "refresh":
                _, _, url = a.get("content", "").partition("url=")
                self.refresh_to = url.strip() or "?"
            key = a.get("name") or a.get("property")
            if key:
                self.meta.setdefault(key, a.get("content", ""))
        elif tag == "link":
            rels = a.get("rel", "").lower().split()
            if "canonical" in rels:
                self.canonical = a.get("href")
            if a.get("href"):
                self.refs.append(a["href"])
        elif tag in ("a", "img", "script", "source", "iframe", "video"):
            for attr in ("href", "src", "poster"):
                if a.get(attr):
                    self.refs.append(a[attr])

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


class Report:
    def __init__(self, quiet: bool = False) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.quiet = quiet

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")

    def info(self, msg: str) -> None:
        if not self.quiet:
            print(msg)


def url_for(page: Path) -> str:
    """journal/foo/index.html -> /journal/foo/ ; index.html -> /"""
    rel = page.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def all_pages() -> list[Path]:
    pages: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name.endswith(".html") and not is_skipped(name):
                pages.append(Path(dirpath) / name)
    return sorted(pages)


def is_skipped(name: str) -> bool:
    return any(fnmatch(name, pattern) for pattern in SKIP_FILES)


def resolve(ref: str, page: Path) -> Path | None:
    """Путь в файловой системе для внутренней ссылки, либо None если ссылка внешняя."""
    ref = ref.strip()
    if not ref or ref.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    parts = urlsplit(ref)
    if parts.scheme or parts.netloc:
        # Абсолютные ссылки на собственный домен тоже проверяем.
        if f"{parts.scheme}://{parts.netloc}" != SITE:
            return None
        path = parts.path or "/"
    else:
        path = parts.path
    if not path:
        return None
    if path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = (page.parent / path).resolve()
    return target


def exists(target: Path) -> bool:
    if target.is_dir():
        return (target / "index.html").is_file()
    if target.is_file():
        return True
    # Путь без слэша в конце, но это каталог со страницей.
    return (Path(str(target)) / "index.html").is_file()


def check_page(page: Path, rep: Report, sitemap_urls: set[str]) -> None:
    where = page.relative_to(ROOT).as_posix()
    html = page.read_text(encoding="utf-8", errors="replace")
    p = Page()
    p.feed(html)

    expected = SITE + url_for(page)
    is_article = where.startswith("journal/") and where.endswith("/index.html")

    for match in sorted(set(PLACEHOLDER_RE.findall(html))):
        rep.error(where, f"незаменённый плейсхолдер шаблона: {match}")

    # Страница-редирект: проверяем только что цель существует и её нет в sitemap.
    if p.is_redirect:
        target = resolve(p.refresh_to or "", page)
        if target is not None and not exists(target):
            rep.error(where, f"редирект ведёт в никуда: {p.refresh_to}")
        if not p.noindex:
            rep.warn(where, "страница-редирект без meta robots=noindex")
        if expected in sitemap_urls:
            rep.error(where, "страница-редирект попала в sitemap.xml")
        return

    if p.noindex and expected in sitemap_urls:
        rep.error(where, "страница с noindex попала в sitemap.xml")

    if p.lang != "ru":
        rep.warn(where, f'<html lang> = {p.lang!r}, ожидается "ru"')
    if not p.title.strip():
        rep.error(where, "нет <title>")
    for key in REQUIRED_META:
        if not p.meta.get(key, "").strip():
            rep.error(where, f"нет мета-тега {key}")
    if p.h1_count == 0:
        rep.error(where, "нет <h1>")
    elif p.h1_count > 1:
        rep.warn(where, f"{p.h1_count} тегов <h1>, должен быть один")

    if not p.canonical:
        rep.error(where, "нет rel=canonical")
    elif p.canonical != expected:
        rep.error(where, f"canonical {p.canonical} вместо {expected}")

    og_url = p.meta.get("og:url", "")
    if og_url and og_url != expected:
        rep.error(where, f"og:url {og_url} вместо {expected}")

    og_image = p.meta.get("og:image", "")
    if not og_image:
        # Статьи расходятся по Telegram и соцсетям — картинка обязательна.
        (rep.error if is_article else rep.warn)(where, "нет мета-тега og:image")
    else:
        target = resolve(og_image, page)
        if target is not None and not exists(target):
            rep.error(where, f"og:image не найден: {og_image}")

    seen: set[str] = set()
    for ref in p.refs:
        if ref in seen:
            continue
        seen.add(ref)
        target = resolve(ref, page)
        if target is None:
            continue
        if not exists(target):
            rep.error(where, f"битая внутренняя ссылка: {ref}")

    # Статьи журнала обязаны быть в sitemap.
    if is_article and sitemap_urls and expected not in sitemap_urls:
        rep.error(where, "статья отсутствует в sitemap.xml")


def check_sitemap(rep: Report) -> set[str]:
    path = ROOT / "sitemap.xml"
    if not path.is_file():
        rep.error("sitemap.xml", "файл отсутствует")
        return set()
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        rep.error("sitemap.xml", f"невалидный XML: {exc}")
        return set()

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls: list[str] = []
    for loc in tree.getroot().iterfind(".//sm:loc", ns):
        urls.append((loc.text or "").strip())
    if not urls:  # sitemap без namespace
        urls = [(loc.text or "").strip() for loc in tree.getroot().iterfind(".//loc")]

    seen: set[str] = set()
    for url in urls:
        if url in seen:
            rep.error("sitemap.xml", f"дубль <loc>: {url}")
            continue
        seen.add(url)
        if not url.startswith(SITE):
            rep.error("sitemap.xml", f"чужой домен в <loc>: {url}")
            continue
        target = ROOT / urlsplit(url).path.lstrip("/")
        if not exists(target):
            rep.error("sitemap.xml", f"<loc> ведёт в никуда: {url}")

    for lastmod in tree.getroot().iterfind(".//sm:lastmod", ns):
        value = (lastmod.text or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            rep.warn("sitemap.xml", f"<lastmod> не в формате YYYY-MM-DD: {value}")

    rep.info(f"sitemap.xml: {len(seen)} уникальных URL")
    return seen


def check_rss(rep: Report) -> None:
    path = ROOT / "rss.xml"
    if not path.is_file():
        rep.error("rss.xml", "файл отсутствует")
        return
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        rep.error("rss.xml", f"невалидный XML: {exc}")
        return

    items = tree.getroot().iterfind(".//item")
    seen: set[str] = set()
    count = 0
    for item in items:
        count += 1
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip() or "<без заголовка>"
        if not link:
            rep.error("rss.xml", f"у item нет <link>: {title}")
            continue
        if link in seen:
            rep.error("rss.xml", f"дубль <link>: {link}")
        seen.add(link)
        target = ROOT / urlsplit(link).path.lstrip("/")
        if not exists(target):
            rep.error("rss.xml", f"<link> ведёт в никуда: {link}")
        guid = (item.findtext("guid") or "").strip()
        if guid and guid != link:
            rep.warn("rss.xml", f"guid не совпадает с link: {guid}")
        if not (item.findtext("pubDate") or "").strip():
            rep.warn("rss.xml", f"нет <pubDate>: {title}")

    rep.info(f"rss.xml: {count} записей")


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка целостности сайта timlabs.online")
    parser.add_argument("paths", nargs="*", help="страницы или каталоги; по умолчанию весь сайт")
    parser.add_argument("--quiet", action="store_true", help="печатать только проблемы")
    args = parser.parse_args()

    rep = Report(quiet=args.quiet)
    sitemap_urls = check_sitemap(rep)
    check_rss(rep)

    if args.paths:
        pages: list[Path] = []
        for raw in args.paths:
            target = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
            if target.is_dir():
                pages.extend(
                    sorted(f for f in target.rglob("*.html") if not is_skipped(f.name))
                )
            elif target.is_file():
                pages.append(target)
            else:
                rep.error(raw, "путь не найден")
    else:
        pages = all_pages()

    for page in pages:
        check_page(page, rep, sitemap_urls)

    rep.info(f"страниц проверено: {len(pages)}")

    for line in rep.warnings:
        print(f"WARN  {line}")
    for line in rep.errors:
        print(f"ERROR {line}")

    if rep.errors:
        print(f"\n✗ ошибок: {len(rep.errors)}, предупреждений: {len(rep.warnings)}")
        return 1
    print(f"\n✓ проверка пройдена, предупреждений: {len(rep.warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
