"""Контракт поиска для сценариев приложения и benchmark."""

from collections.abc import Sequence
from typing import Protocol

from app.backend.domain.models import SearchHit


class SearchPort(Protocol):
    def search(
        self,
        query: str,
        *,
        city: str | None,
        limit: int,
        categories: Sequence[str] = (),
        excluded_ids: Sequence[str] = (),
    ) -> Sequence[SearchHit]:
        """Вернуть совпадения по убыванию балла, равные — по строковому ID."""
        ...
