"""Собственный BM25 по формуле и примеру занятия 3."""

from collections import Counter, defaultdict
from collections.abc import Sequence
from math import isfinite, log1p

from app.backend.domain.models import Place, SearchDocument, SearchHit
from app.backend.infrastructure.search.preprocessing import preprocess


class BM25Search:
    def __init__(
        self, places: Sequence[Place | SearchDocument], *, k1: float = 1.2, b: float = 0.75
    ) -> None:
        for name, value in (("k1", k1), ("b", b)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"{name}: нужен конечный числовой параметр")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("Нужны k1 > 0 и 0 <= b <= 1")
        self._k1 = k1
        self._b = b
        self._places: dict[str, Place | SearchDocument] = {}
        self._lengths: dict[str, int] = {}
        self._postings: dict[str, dict[str, int]] = {}
        for place in places:
            if place.id in self._places:
                raise ValueError(f"Повтор ID документа: {place.id}")
            self._places[place.id] = place
            tokens = preprocess(place.text)
            self._lengths[place.id] = len(tokens)
            for term, count in Counter(tokens).items():
                self._postings.setdefault(term, {})[place.id] = count
        self._avgdl = (
            sum(self._lengths.values()) / len(self._places) if self._places else 0.0
        )

    @property
    def document_count(self) -> int:
        return len(self._places)

    @property
    def average_document_length(self) -> float:
        return self._avgdl

    def search(
        self,
        query: str,
        *,
        city: str | None,
        limit: int,
        categories: Sequence[str] = (),
        excluded_ids: Sequence[str] = (),
    ) -> list[SearchHit]:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit должен быть положительным целым числом")
        terms = dict.fromkeys(preprocess(query))
        if not terms or not self._avgdl:
            return []
        city_key = city.strip().casefold() if city is not None else None
        categories_set = set(categories)
        excluded_set = set(excluded_ids)
        scores: dict[str, float] = defaultdict(float)
        for term in terms:
            postings = self._postings.get(term, {})
            df = len(postings)
            if not df:
                continue
            idf = log1p((self.document_count - df + 0.5) / (df + 0.5))
            for place_id, tf in postings.items():
                place = self._places[place_id]
                if place_id in excluded_set:
                    continue
                if city_key is not None and place.city.strip().casefold() != city_key:
                    continue
                if categories_set and place.category not in categories_set:
                    continue
                norm = self._k1 * (
                    1 - self._b + self._b * self._lengths[place_id] / self._avgdl
                )
                scores[place_id] += idf * tf * (self._k1 + 1) / (tf + norm)
        ranked = sorted(scores, key=lambda place_id: (-scores[place_id], place_id))
        return [SearchHit(place=self._places[place_id], score=scores[place_id]) for place_id in ranked[:limit]]
