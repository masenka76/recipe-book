"""Единая схема рецепта — общий формат для всех источников (скрейпер, Claude, ручной ввод)."""

from __future__ import annotations

import datetime as _dt
from typing import Optional

from pydantic import BaseModel, Field
from slugify import slugify


class Recipe(BaseModel):
    """Нормализованный рецепт. Именно этот объект рендерится в Markdown и PDF."""

    title: str = Field(description="Название блюда")
    ingredients: list[str] = Field(
        default_factory=list,
        description="Список ингредиентов, по одной строке на позицию, с количеством",
    )
    steps: list[str] = Field(
        default_factory=list,
        description="Шаги приготовления по порядку, без нумерации в тексте",
    )

    servings: Optional[str] = Field(default=None, description="Количество порций, например «4 порции»")
    total_time: Optional[str] = Field(default=None, description="Общее время, например «45 минут»")
    yields: Optional[str] = Field(default=None, description="Выход, например «1 форма 24 см»")

    notes: Optional[str] = Field(default=None, description="Заметки, советы, вариации")
    tags: list[str] = Field(default_factory=list, description="Метки: категория, кухня, повод")

    source_url: Optional[str] = Field(default=None, description="Исходная ссылка")
    source_name: Optional[str] = Field(default=None, description="Название сайта или автора")
    image_url: Optional[str] = Field(default=None, description="Ссылка на фото блюда")
    language: Optional[str] = Field(default=None, description="Язык рецепта, ISO-код: ru, en, …")

    date_added: str = Field(
        default_factory=lambda: _dt.date.today().isoformat(),
        description="Дата добавления в книгу, ISO",
    )

    def slug(self) -> str:
        """Стабильный slug для имени файла: транслит названия + дата."""
        base = slugify(self.title, max_length=60) or "recipe"
        return f"{base}-{self.date_added}"

    def normalized_tags(self) -> list[str]:
        """Теги в нижнем регистре, без дублей, порядок сохранён."""
        seen: set[str] = set()
        out: list[str] = []
        for tag in self.tags:
            t = tag.strip().lstrip("#").lower()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out
