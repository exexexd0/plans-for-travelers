"""Общие модели поиска без зависимостей от HTTP и файлов."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class Place:
    id: str
    name: str
    city: str
    text: str
    lat: float | None = None
    lon: float | None = None
    source: str | None = None
    category: str | None = None
    address: str | None = None

    def __post_init__(self) -> None:
        for field in ("id", "name", "city"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field}: нужна непустая строка")
        if not isinstance(self.text, str):
            raise ValueError("text: нужна строка")
        for field in ("source", "category", "address"):
            value = getattr(self, field)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{field}: нужна строка или null")
        for field, bound in (("lat", 90), ("lon", 180)):
            value = getattr(self, field)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or not -bound <= value <= bound
            ):
                raise ValueError(f"{field}: неверная координата")


@dataclass(frozen=True, slots=True)
class SearchDocument:
    """Единица поиска: подборка мест одной категории, без общей координаты."""

    id: str
    name: str
    city: str
    text: str
    category: str
    places: tuple[Place, ...]

    def __post_init__(self) -> None:
        for field in ("id", "name", "city", "category", "text"):
            if not isinstance(getattr(self, field), str) or not getattr(self, field).strip():
                raise ValueError(f"{field}: нужна непустая строка")
        if not self.places or any(not isinstance(p, Place) for p in self.places):
            raise ValueError("places: нужен непустой список мест")
        if any(p.city != self.city or p.category != self.category for p in self.places):
            raise ValueError("Все места подборки должны иметь её город и категорию")
        if len({p.id for p in self.places}) != len(self.places):
            raise ValueError("Повтор ID места внутри подборки")


@dataclass(frozen=True, slots=True)
class SearchHit:
    place: Place | SearchDocument
    score: float
