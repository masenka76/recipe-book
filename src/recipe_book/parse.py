"""Разбор рецепта из ссылки или произвольного текста в объект :class:`Recipe`.

Стратегия:
1. Если это ссылка — сначала пробуем ``recipe-scrapers`` (быстро, без затрат на API).
2. Если скрейпер не справился или на вход дан свободный текст — просим Claude
   извлечь структуру.
"""

from __future__ import annotations

import os
import re

import httpx

from .schema import Recipe

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_MODEL = os.environ.get("RECIPE_MODEL", "claude-opus-5")

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def looks_like_url(text: str) -> bool:
    return bool(_URL_RE.match(text.strip()))


def parse(source: str, *, tags: list[str] | None = None, model: str = DEFAULT_MODEL) -> Recipe:
    """Главная точка входа: ссылка или текст → :class:`Recipe`."""
    source = source.strip()
    tags = tags or []

    if looks_like_url(source):
        recipe = _from_scraper(source)
        if recipe is None:
            html = _fetch(source)
            recipe = _from_claude(_visible_text(html), url=source, model=model)
    else:
        recipe = _from_claude(source, url=None, model=model)

    recipe.tags = [*recipe.tags, *tags]
    return recipe


# --------------------------------------------------------------------------- #
# Ветка recipe-scrapers
# --------------------------------------------------------------------------- #
def _from_scraper(url: str) -> Recipe | None:
    try:
        from recipe_scrapers import scrape_html
    except ImportError:  # pragma: no cover
        return None

    try:
        html = _fetch(url)
        scraper = scrape_html(html, org_url=url, wild_mode=True)
    except Exception:
        return None

    def _try(fn, default=None):
        try:
            value = fn()
            return value if value else default
        except Exception:
            return default

    title = _try(scraper.title)
    ingredients = _try(scraper.ingredients, []) or []
    steps_raw = _try(scraper.instructions, "") or ""
    steps = [s.strip() for s in steps_raw.split("\n") if s.strip()]

    # Без названия или без сути рецепта считаем, что скрейпер не справился.
    if not title or not ingredients or not steps:
        return None

    return Recipe(
        title=title,
        ingredients=[i.strip() for i in ingredients if i.strip()],
        steps=steps,
        servings=_try(scraper.yields),
        total_time=_format_minutes(_try(scraper.total_time)),
        notes=_try(getattr(scraper, "description", lambda: None)),
        source_url=url,
        source_name=_try(scraper.host),
        image_url=_try(scraper.image),
        language=_try(getattr(scraper, "language", lambda: None)),
    )


def _format_minutes(value) -> str | None:
    if not value:
        return None
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return str(value)
    if minutes <= 0:
        return None
    if minutes < 60:
        return f"{minutes} мин"
    hours, rest = divmod(minutes, 60)
    return f"{hours} ч {rest} мин" if rest else f"{hours} ч"


# --------------------------------------------------------------------------- #
# Ветка Claude
# --------------------------------------------------------------------------- #
_SYSTEM = (
    "Ты извлекаешь структуру рецепта из текста веб-страницы или заметки. "
    "Пиши на языке оригинала рецепта. Ингредиенты — по одной строке с количеством. "
    "Шаги — по порядку, без нумерации в самом тексте. Если поля нет — оставь пустым. "
    "Придумай 2–5 полезных тегов (категория блюда, кухня, повод), если их нет в тексте."
)


def _from_claude(content: str, *, url: str | None, model: str) -> Recipe:
    import anthropic

    if not content.strip():
        raise ValueError("Пустой текст рецепта — нечего разбирать.")

    client = anthropic.Anthropic()
    user = content if not url else f"Источник: {url}\n\n{content}"

    response = client.messages.parse(
        model=model,
        max_tokens=8000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user[:120_000]}],
        output_format=Recipe,
    )
    recipe: Recipe = response.parsed_output
    if url and not recipe.source_url:
        recipe.source_url = url
    return recipe


# --------------------------------------------------------------------------- #
# HTTP + чистка HTML
# --------------------------------------------------------------------------- #
def _fetch(url: str, timeout: float = 20.0) -> str:
    resp = httpx.get(
        url,
        follow_redirects=True,
        timeout=timeout,
        headers={"User-Agent": _UA, "Accept-Language": "ru,en;q=0.8"},
    )
    resp.raise_for_status()
    return resp.text


def _visible_text(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)
