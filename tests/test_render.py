from recipe_book.render import to_markdown
from recipe_book.schema import Recipe


def _sample() -> Recipe:
    return Recipe(
        title="Блины на молоке",
        ingredients=["2 яйца", "500 мл молока", "200 г муки"],
        steps=["Смешать яйца с молоком", "Ввести муку", "Жарить на среднем огне"],
        servings="4 порции",
        tags=["#Завтрак", "завтрак", " Быстро "],
        source_url="https://example.com/bliny",
        date_added="2026-09-01",
    )


def test_slug_is_stable_and_transliterated():
    assert _sample().slug() == "bliny-na-moloke-2026-09-01"


def test_tags_normalized_without_duplicates():
    assert _sample().normalized_tags() == ["завтрак", "быстро"]


def test_markdown_has_front_matter_and_sections():
    md = to_markdown(_sample())
    assert md.startswith("---\n")
    assert "title: Блины на молоке" in md
    assert "## Ингредиенты" in md
    assert "1. Смешать яйца с молоком" in md
    assert "[Источник](https://example.com/bliny)" in md
