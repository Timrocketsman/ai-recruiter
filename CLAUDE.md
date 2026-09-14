# TimLabs — timlabs.online

Статический сайт без сборки: HTML отдаётся как есть. Ни npm, ни pip, ни бандлера —
правки идут прямо в `.html`. Публикация через GitHub Pages, домен задан файлом `CNAME`.

## Структура

```
index.html                  главная
journal/index.html          лента журнала «Компас»
journal/<slug>/index.html   статья журнала
<slug>/index.html           посадочная страница услуги (massage-kislovodsk, retrit-otshelnik, …)
media/telegram/<slug>.png   обложка статьи для соцсетей (og:image)
sitemap.xml                 карта сайта
rss.xml                     фид журнала (только свежие записи, не весь архив)
scripts/check_site.py       проверка целостности сайта
```

## Проверки

Единственный линтер и тест проекта — `scripts/check_site.py`, только стандартная
библиотека Python, работает одинаково на маке и в веб-сессии:

```bash
python3 scripts/check_site.py                       # весь сайт, ~0.5 с
python3 scripts/check_site.py journal/<slug>        # одна статья
python3 scripts/check_site.py --quiet               # только проблемы
```

Проверяет: обязательные мета-теги, совпадение `canonical`/`og:url` с реальным путём,
ровно один `<h1>`, незаменённые плейсхолдеры `{{…}}`, битые внутренние ссылки и
картинки, валидность и согласованность `sitemap.xml` и `rss.xml`.

Гонять перед каждым коммитом. `ERROR` — блокирует коммит, `WARN` — на усмотрение.

Локальный просмотр:

```bash
python3 -m http.server 8000     # затем http://localhost:8000/journal/<slug>/
```

## Новая статья журнала

1. `journal/<slug>/index.html` — за образец брать соседнюю свежую статью.
2. В `<head>` обязательны: `<title>`, `meta description`, `link rel=canonical`,
   `og:type|title|description|url|image`, JSON-LD с `BreadcrumbList` + `BlogPosting`
   (и `FAQPage`, если в статье есть блок вопросов).
3. `canonical` и `og:url` — ровно `https://timlabs.online/journal/<slug>/`, со слэшем на конце.
4. Обложка `media/telegram/<slug>.png`, на неё же указывает `og:image`. Без неё линтер упадёт.
5. Добавить запись в `sitemap.xml` (`<loc>` + `<lastmod>` в формате `YYYY-MM-DD`).
6. Добавить `<item>` в начало `rss.xml`: `title`, `link`, `guid` (равен `link`),
   `pubDate` в RFC 822, `description` в CDATA, `category`, `enclosure` и `media:content`
   на обложку, `content:encoded` с телом статьи. Обновить `lastBuildDate` канала.
7. Прогнать `python3 scripts/check_site.py`.

## Удалённая или переехавшая страница

Вместо удаления файла — заглушка-редирект: `<meta http-equiv="refresh" content="0; url=…">`,
`<meta name="robots" content="noindex">`, `canonical` на новый адрес. Такую страницу
нужно убрать из `sitemap.xml` — линтер это проверяет.

## Работа с двух устройств

Дома мак, на улице телефон — работают с одним и тем же репозиторием через веб-сессии
Claude Code (claude.ai/code). Веб-сессия живёт в собственном контейнере и доступна
с любого устройства.

Не использовать для кросс-девайсной работы локальные CLI-сессии на маке: они
привязаны к процессу на ноутбуке, и с телефона открываются с ошибками или зависают,
как только мак уснул или CLI закрыт.

## Правила коммитов

- Ветка `main` — то, что опубликовано. Правки идут через отдельную ветку.
- Один коммит — одна законченная правка (статья целиком, вместе с `sitemap.xml` и `rss.xml`).
- Сообщения коммитов на русском, в стиле уже существующих: `журнал: статья /journal/<slug>/`.
