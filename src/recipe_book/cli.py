"""CLI: ``recipe add <ссылка|текст> [--tags ...]``.

Фаза 1 — локальный конвейер: разобрать рецепт, сохранить .md в repo, собрать PDF в out/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._bootstrap import ensure_native_libs

ensure_native_libs()  # может перезапустить процесс — держим до тяжёлых импортов

from . import __version__
from .parse import parse
from .render import to_pdf
from .store import rebuild_index, save_markdown

OUT_DIR = Path.cwd() / "out"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="recipe", description="Книга рецептов → PDF")
    parser.add_argument("--version", action="version", version=f"recipe-book {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Добавить рецепт по ссылке или из текста")
    add.add_argument("source", help="URL рецепта или сам текст рецепта")
    add.add_argument(
        "-t", "--tags", default="", help="Метки через запятую, например: выпечка,быстро"
    )
    add.add_argument("--no-pdf", action="store_true", help="Только .md, без PDF")
    add.add_argument("--model", default=None, help="Переопределить модель Claude")

    sub.add_parser("reindex", help="Пересобрать INDEX.md")

    args = parser.parse_args(argv)

    if args.command == "reindex":
        path = rebuild_index()
        print(f"Обновлён {path}")
        return 0

    if args.command == "add":
        return _cmd_add(args)

    return 1


def _cmd_add(args: argparse.Namespace) -> int:
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    kwargs = {"tags": tags}
    if args.model:
        kwargs["model"] = args.model

    try:
        recipe = parse(args.source, **kwargs)
    except Exception as exc:  # noqa: BLE001 — на входе пользовательский CLI
        print(f"Не удалось разобрать рецепт: {exc}", file=sys.stderr)
        return 1

    md_path = save_markdown(recipe)
    print(f"Сохранён рецепт:  {_rel(md_path)}")

    index_path = rebuild_index()
    print(f"Обновлён индекс:  {index_path.name}")

    if not args.no_pdf:
        pdf_path = to_pdf(recipe, OUT_DIR / f"{recipe.slug()}.pdf")
        print(f"Готов PDF:        {_rel(pdf_path)}")

    print()
    print(f"  {recipe.title}")
    print(f"  метки: {', '.join(recipe.normalized_tags()) or '—'}")
    print(f"  ингредиентов: {len(recipe.ingredients)}, шагов: {len(recipe.steps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
