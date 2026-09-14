#!/bin/bash
# SessionStart-хук для Claude Code на вебе и телефоне.
#
# Сайт статический: собирать и ставить нечего. Задача хука — убедиться, что
# в контейнере есть всё для проверок и локального просмотра, положить в сессию
# переменные окружения и сразу показать состояние сайта.
set -euo pipefail

# На маке всё уже установлено — хук нужен только удалённым сессиям.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$PROJECT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "session-start: python3 не найден — проверки сайта работать не будут" >&2
  exit 1
fi

echo "session-start: python3 $(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"

# Переменные доступны во всех последующих командах сессии.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export SITE_URL=https://timlabs.online"
    echo "export SITE_ROOT=$PROJECT_DIR"
    echo "export PYTHONDONTWRITEBYTECODE=1"
  } >> "$CLAUDE_ENV_FILE"
fi

# Состояние сайта на старте сессии: сразу видно, чистая ли ветка.
echo "session-start: проверка целостности сайта"
if python3 scripts/check_site.py --quiet; then
  :
else
  echo "session-start: проверка нашла ошибки (см. выше) — почини их перед коммитом" >&2
fi

echo "session-start: готово. Проверка — python3 scripts/check_site.py, просмотр — python3 -m http.server 8000"
