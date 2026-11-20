"""Однодневный маршрут: собственный BM25 → выбор LLM → пеший OSRM."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException

from app.backend.domain.models import SearchDocument
from app.backend.api.schemas import DayRoute, LineString, RouteDay, Stop, TripRequest, TripResponse
from app.backend.infrastructure.corpus.loader import load_places
from app.backend.infrastructure.llm.client import LlmSelector
from app.backend.infrastructure.search.bm25 import BM25Search
from app.pipeline.rag.routing import OsrmRouter

INTEREST_LABELS = {
    "kids": "Прогулка с детьми", "food": "Кафе и еда по пути",
    "nature": "Природа и парки", "buildings": "Красивые здания",
    "art": "Выставки и галереи", "active": "Активный отдых", "unusual": "Необычные места",
}


def pipeline_query(request: TripRequest) -> str:
    query = f"Город: {request.city}. Интересы: " + ", ".join(INTEREST_LABELS[key] for key in request.interests) + "."
    if request.prompt and request.prompt.strip():
        query += " Пожелания пользователя: " + request.prompt.strip()
    return query


def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Декодировать стандартный OSRM polyline5 в порядок GeoJSON: долгота, широта."""
    coordinates = []
    index = latitude = longitude = 0
    while index < len(encoded):
        values = []
        for _ in range(2):
            value = shift = 0
            while True:
                if index >= len(encoded) or shift > 30:
                    raise ValueError("Некорректная геометрия маршрута")
                char = ord(encoded[index]) - 63
                index += 1
                if not 0 <= char <= 63:
                    raise ValueError("Некорректная геометрия маршрута")
                value |= (char & 31) << shift
                shift += 5
                if char < 32:
                    break
            values.append(~(value >> 1) if value & 1 else value >> 1)
        latitude += values[0]
        longitude += values[1]
        coordinates.append((longitude / 100000, latitude / 100000))
    return coordinates


class PipelineTripGenerator:
    def __init__(self, documents: list[SearchDocument], selector: LlmSelector, router: OsrmRouter):
        self.index = BM25Search(documents, k1=1.2, b=0.75)
        self.selector = selector
        self.router = router
        self.cities = {p.city.strip().casefold() for p in documents}

    async def generate(self, request: TripRequest) -> TripResponse:
        if request.city.strip().casefold() not in self.cities:
            raise HTTPException(status_code=422, detail="Для выбранного города нет данных.")
        query = pipeline_query(request)
        hits = self.index.search(query, city=request.city, limit=3)
        places = {p.id: p for hit in hits for p in hit.place.places
                  if p.lat is not None and p.lon is not None}
        if not places:
            raise HTTPException(status_code=422, detail="Подходящие места не найдены.")
        selection = await self.selector.select(query, request.start, hits)
        if len(selection.place_ids) != len(set(selection.place_ids)):
            raise ValueError("LLM повторила место")
        if any(id not in places for id in selection.place_ids):
            raise ValueError("LLM выбрала неизвестное место")
        chosen = [places[id] for id in selection.place_ids]
        stops = [Stop(id=p.id, name=p.name, address=p.address, description=p.text,
                      latitude=p.lat, longitude=p.lon) for p in chosen]
        route = None
        if len(chosen) > 1:
            points = [{"org_id": p.id, "name": p.name, "lat": p.lat, "lon": p.lon,
                       "category": p.category} for p in chosen]
            routed = await self.router.route(points, "foot")
            geometry = decode_polyline(routed.geometry)
            if len(geometry) < 2:
                raise RuntimeError("OSRM не вернул геометрию маршрута")
            route = DayRoute(geometry=LineString(coordinates=geometry))
        summary = "Места: " + ", ".join(p.name for p in chosen) + "."
        if selection.insufficient_places:
            summary += " Тестовый режим, мест пока не много"
        day = RouteDay(date=request.start, title=selection.title, summary=summary,
                       stops=stops, route=route)
        return TripResponse(city=request.city, description=summary, days=[day])


def create_pipeline_generator() -> PipelineTripGenerator:
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    corpus = Path(os.environ.get("CORPUS_PATH", "app/backend/data/ivanovo"))
    if not corpus.is_absolute():
        corpus = root / corpus
    documents = load_places(corpus)
    selector = LlmSelector(
        api_key=os.environ.get("ROUTERAI_API_KEY", ""),
        base_url=os.environ.get("ROUTERAI_BASE_URL", "https://routerai.ru/api/v1"),
        model=os.environ.get("CHAT_MODEL", "openai/gpt-4o-mini"),
    )
    return PipelineTripGenerator(documents, selector, OsrmRouter(
        os.environ.get("OSRM_BASE_URL", "http://127.0.0.1:5000")))
