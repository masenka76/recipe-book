"""Рендер :class:`Recipe` в Markdown и в PDF (HTML-шаблон → WeasyPrint)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .schema import Recipe

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def to_markdown(recipe: Recipe) -> str:
    """Каноничная копия рецепта для хранения в репозитории."""
    lines: list[str] = []
    front = [
        "---",
        f"title: {_yaml(recipe.title)}",
        f"date_added: {recipe.date_added}",
        f"tags: [{', '.join(recipe.normalized_tags())}]",
    ]
    if recipe.source_url:
        front.append(f"source_url: {recipe.source_url}")
    if recipe.source_name:
        front.append(f"source_name: {_yaml(recipe.source_name)}")
    if recipe.servings:
        front.append(f"servings: {_yaml(recipe.servings)}")
    if recipe.total_time:
        front.append(f"total_time: {_yaml(recipe.total_time)}")
    front.append("---")
    lines.extend(front)
    lines.append("")
    lines.append(f"# {recipe.title}")
    lines.append("")

    meta = [m for m in (recipe.servings, recipe.total_time, recipe.yields) if m]
    if meta:
        lines.append("*" + " · ".join(meta) + "*")
        lines.append("")

    lines.append("## Ингредиенты")
    lines.append("")
    lines.extend(f"- {item}" for item in recipe.ingredients)
    lines.append("")

    lines.append("## Приготовление")
    lines.append("")
    lines.extend(f"{i}. {step}" for i, step in enumerate(recipe.steps, 1))
    lines.append("")

    if recipe.notes:
        lines.append("## Заметки")
        lines.append("")
        lines.append(recipe.notes)
        lines.append("")

    if recipe.source_url:
        lines.append(f"[Источник]({recipe.source_url})")
        lines.append("")

    return "\n".join(lines)


def to_pdf(recipe: Recipe, out_path: Path) -> Path:
    """Сгенерировать PDF по HTML-шаблону."""
    from weasyprint import HTML

    template = _env.get_template("recipe.html.j2")
    html = template.render(recipe=recipe, tags=recipe.normalized_tags())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf(str(out_path))
    return out_path


def _yaml(value: str) -> str:
    """Простое экранирование строки для YAML front matter."""
    if any(c in value for c in ':#"\n') or value != value.strip():
        return '"' + value.replace('"', '\\"') + '"'
    return value
