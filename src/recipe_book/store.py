"""Хранение рецептов в репозитории: файлы ``recipes/<slug>.md`` и сводный ``INDEX.md``."""

from __future__ import annotations

import re
from pathlib import Path

from .render import to_markdown
from .schema import Recipe

REPO_ROOT = Path(__file__).resolve().parents[2]
RECIPES_DIR = REPO_ROOT / "recipes"
INDEX_FILE = REPO_ROOT / "INDEX.md"

_FRONT_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def save_markdown(recipe: Recipe) -> Path:
    """Записать каноничную копию рецепта. Возвращает путь к файлу."""
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    path = RECIPES_DIR / f"{recipe.slug()}.md"
    path.write_text(to_markdown(recipe), encoding="utf-8")
    return path


def rebuild_index() -> Path:
    """Пересобрать INDEX.md по всем файлам в recipes/."""
    rows: list[tuple[str, str, str, str]] = []  # (title, date, tags, filename)
    for md in sorted(RECIPES_DIR.glob("*.md")):
        meta = _read_front_matter(md.read_text(encoding="utf-8"))
        rows.append(
            (
                meta.get("title", md.stem),
                meta.get("date_added", ""),
                meta.get("tags", ""),
                md.name,
            )
        )

    rows.sort(key=lambda r: (r[1], r[0]), reverse=True)

    lines = ["# Книга рецептов", "", f"Всего рецептов: {len(rows)}", "", "| Дата | Рецепт | Метки |", "| --- | --- | --- |"]
    for title, date, tags, filename in rows:
        link = f"[{title}](recipes/{filename})"
        lines.append(f"| {date} | {link} | {tags} |")
    lines.append("")

    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")
    return INDEX_FILE


def _read_front_matter(text: str) -> dict[str, str]:
    match = _FRONT_RE.match(text)
    if not match:
        return {}
    out: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
        out[key.strip()] = value.strip().strip('"')
    return out
