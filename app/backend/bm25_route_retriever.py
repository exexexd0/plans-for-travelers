"""BM25-кандидаты для каждой остановки маршрутного графа."""

import logging

from app.backend.domain.models import SearchDocument
from app.backend.infrastructure.search.bm25 import BM25Search
from app.backend.infrastructure.search.preprocessing import preprocess
from app.pipeline.rag.categories import CATEGORY_LABELS, classify_rubric

logger = logging.getLogger("uvicorn.error.bm25")


class BM25RouteRetriever:
    def __init__(self, documents: list[SearchDocument], document_index: BM25Search):
        self.documents = documents
        self.document_index = document_index
        self.place_index = BM25Search([place for document in documents for place in document.places])
        self.place_documents = {place.id: document.id for document in documents for place in document.places}

    async def search(self, *, user_query: str, city: str, category: str,
                     excluded_org_ids: list[str]) -> list[dict]:
        if category == "sight":
            # В текущем корпусе архитектурные здания могут находиться в культурных подборках.
            # Без упоминания здания не считаем культурное учреждение зданием-достопримечательностью.
            categories = {document.category for document in self.documents
                          if classify_rubric(document.category)[0] == "sight" or
                          (classify_rubric(document.category)[0] == "culture" and
                           any({"здание", "архитектура"} & set(preprocess(place.text)) for place in document.places))}
            query = "Красивые здания " + CATEGORY_LABELS[category]
        else:
            categories = {document.category for document in self.documents
                          if classify_rubric(document.category)[0] == category}
            query = CATEGORY_LABELS[category]
        if not categories:
            return []
        query += " " + user_query
        hits = self.document_index.search(query, city=city, limit=3, categories=tuple(categories))
        found_documents = {hit.place.id for hit in hits}
        logger.info("BM25 цель=%s документы=%s", category,
                    [(hit.place.id, round(hit.score, 4)) for hit in hits])
        if not found_documents:
            return []
        ranked_places = self.place_index.search(query, city=city,
                                                limit=self.place_index.document_count,
                                                categories=tuple(categories),
                                                excluded_ids=excluded_org_ids)
        candidates = []
        for hit in ranked_places:
            place = hit.place
            document_id = self.place_documents[place.id]
            if document_id not in found_documents or place.lat is None or place.lon is None:
                continue
            if category == "sight" and classify_rubric(place.category)[0] != "sight" and not ({"здание", "архитектура"} & set(preprocess(place.text))):
                continue
            candidates.append({"org_id": place.id, "name": place.name, "city": place.city,
                               "address": place.address, "type": place.category, "text": place.text,
                               "source": place.source, "document_id": document_id,
                               "lat": place.lat, "lon": place.lon, "category": category,
                               "rating": None, "distance": None, "bm25_score": hit.score})
            if len(candidates) == 5:
                break
        return candidates
