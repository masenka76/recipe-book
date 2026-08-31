# recipe-book

Присылаешь ссылку на рецепт или его текст — получаешь аккуратный PDF и каноничную
копию в Markdown. Итоговая цель: Telegram-бот → GitHub Actions → PDF в Google Drive
с метками.

## Как это будет работать

```
Telegram (ссылка / текст боту)
   │  раз в ~10 мин
GitHub Actions (cron)
   ├─ парсинг: recipe-scrapers → если не вышло, Claude
   ├─ нормализация в единую схему (schema.Recipe)
   ├─ коммит recipes/<slug>.md + пересборка INDEX.md
   ├─ генерация PDF (HTML-шаблон + WeasyPrint)
   ├─ загрузка PDF в Google Drive в нужную папку + метки
   └─ ответ в Telegram: ссылка на PDF + сводка
```

## Дорожная карта

| Фаза | Содержание | Статус |
| --- | --- | --- |
| 1 | Локальный CLI: ссылка/текст → `recipes/<slug>.md` + PDF в `out/` | ✅ готово |
| 2 | Загрузка PDF в Google Drive + метки (OAuth refresh token) | ⏳ |
| 3 | Приём рецептов из Telegram | ⏳ |
| 4 | GitHub Actions: cron-поллинг Telegram, секреты | ⏳ |
| 5 | Полировка шаблона PDF, обработка ошибок | ⏳ |

## Фаза 1 — локальный запуск

Требуется Python ≥ 3.11 и системная библиотека Pango (для WeasyPrint).

```bash
# однократно: библиотека для рендера PDF
brew install pango

# окружение (используется uv; можно и обычный python -m venv)
uv venv --python 3.12
uv pip install -e .

# добавить рецепт по ссылке
recipe add "https://www.bbcgoodfood.com/recipes/easy-chocolate-cake" --tags "десерт,выпечка"

# добавить рецепт из текста (нужен ключ Claude, см. ниже)
recipe add "Блины на молоке: 2 яйца, 500 мл молока, 200 г муки ..." --tags "завтрак"

# только Markdown, без PDF
recipe add "<ссылка>" --no-pdf

# пересобрать INDEX.md
recipe reindex
```

Результат:

- `recipes/<slug>.md` — каноничная копия рецепта (коммитится в репозиторий);
- `INDEX.md` — сводная таблица всех рецептов с метками;
- `out/<slug>.pdf` — сгенерированный PDF (в `.gitignore`).

### Ключ Claude

Нужен только для разбора произвольного текста и сайтов без поддержки `recipe-scrapers`.
Способы аутентификации (порядок приоритета в SDK): переменная `ANTHROPIC_API_KEY`
либо профиль `ant auth login`.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Модель по умолчанию — `claude-opus-5`. Переопределяется переменной `RECIPE_MODEL`
или флагом `--model` (например `RECIPE_MODEL=claude-sonnet-5`).

## Структура

```
src/recipe_book/
  schema.py   единая модель Recipe + slug + нормализация тегов
  parse.py    ссылка/текст → Recipe (recipe-scrapers, затем Claude)
  render.py   Recipe → Markdown и Recipe → PDF
  store.py    запись recipes/*.md и пересборка INDEX.md
  cli.py      команда `recipe`
templates/
  recipe.html.j2 / recipe.css   вёрстка PDF
recipes/      архив рецептов в Markdown
```
