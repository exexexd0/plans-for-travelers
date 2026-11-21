"""Однодневный маршрут: собственный BM25 → выбор LLM → пеший OSRM."""

import os
from types import SimpleNamespace
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException

from app.backend.domain.models import SearchDocument
from app.backend.api.schemas import DayRoute, LineString, RouteDay, Stop, TripRequest, TripResponse
from app.backend.infrastructure.corpus.loader import load_places
from app.backend.bm25_route_retriever import BM25RouteRetriever
from app.backend.infrastructure.search.bm25 import BM25Search
from app.pipeline.rag.categories import CANONICAL_CATEGORIES, CATEGORY_LABELS
from app.pipeline.rag.graph import build_route_graph, initial_state, route_view, validate_route
from app.pipeline.rag.jev import JevSelector
from app.pipeline.rag.planner import LlmPlanner
from app.pipeline.rag.routing import OsrmRouter

INTEREST_LABELS = {
    "kids": "Прогулка с детьми", "food": "Кафе и еда по пути",
    "nature": "Природа и парки", "buildings": "Красивые здания",
    "art": "Выставки и галереи", "active": "Активный отдых", "unusual": "Необычные места",
}


# Для явно выбранных интересов с однозначной категорией не полагаемся на то,
# что планировщик обязательно их повторит. Остальные цели он определяет по запросу.
REQUIRED_CATEGORIES = {"food": "food", "nature": "nature", "buildings": "sight", "art": "culture"}


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
    def __init__(self, documents: list[SearchDocument], planner, selector, router):
        self.index = BM25Search(documents, k1=1.2, b=0.75)
        self.retriever = BM25RouteRetriever(documents, self.index)
        self.planner = planner
        self.selector = selector
        self.router = router
        self.cities = {document.city.strip().casefold() for document in documents}

    async def generate(self, request: TripRequest) -> TripResponse:
        if request.city.strip().casefold() not in self.cities:
            raise HTTPException(status_code=422, detail="Для выбранного города нет данных.")
        required = tuple(dict.fromkeys(REQUIRED_CATEGORIES[id] for id in request.interests
                                       if id in REQUIRED_CATEGORIES))
        graph = build_route_graph(self.planner, self.retriever, self.selector, router=self.router,
                                  allow_ranked_fallback=False, required_categories=required)
        state = await graph.ainvoke(initial_state(pipeline_query(request), request.city,
                                                   list(CANONICAL_CATEGORIES)))
        payload = route_view(state)
        if payload.get("stopped_reason") == "no_candidates":
            raise HTTPException(status_code=422, detail="Подходящие места не найдены.")
        validate_route(payload)
        sources = {place["org_id"]: place for step in payload["steps"]
                   for place in (step.get("primary"), step.get("backup"))
                   if place and place.get("org_id")}
        points = payload["waypoints"]
        if not points or any(point["place_id"] not in sources for point in points):
            raise ValueError("Маршрут содержит неизвестное место")
        if len({point["place_id"] for point in points}) != len(points):
            raise ValueError("В маршруте есть повторяющиеся места")
        stops = [Stop(id=str(point["place_id"]), name=point["name"],
                      address=sources[point["place_id"]].get("address"),
                      description=sources[point["place_id"]].get("type"),
                      latitude=point["lat"], longitude=point["lon"])
                 for point in points]
        geometry = decode_polyline(payload.get("route_geometry") or "")
        route = DayRoute(geometry=LineString(coordinates=geometry)) if len(geometry) >= 2 else None
        summary = "Места: " + ", ".join(stop.name for stop in stops) + "."
        if payload.get("missing_categories"):
            summary += " Тестовый режим, мест пока не много. Не удалось подобрать: " + ", ".join(
                CATEGORY_LABELS[category] for category in payload["missing_categories"]) + "."
        day = RouteDay(date=request.start, title=payload["route_title"], summary=summary,
                       stops=stops, route=route)
        return TripResponse(city=request.city, description=summary, days=[day])


def create_pipeline_generator() -> PipelineTripGenerator:
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    corpus = Path(os.environ.get("CORPUS_PATH", "app/backend/data/ivanovo"))
    if not corpus.is_absolute():
        corpus = root / corpus
    documents = load_places(corpus)
    base_url = os.environ.get("ROUTERAI_BASE_URL", "https://routerai.ru/api/v1").rstrip("/")
    settings = SimpleNamespace(
        routerai_api_key=os.environ.get("ROUTERAI_API_KEY", ""),
        routerai_base_url=base_url,
        chat_model=os.environ.get("CHAT_MODEL", "openai/gpt-4o-mini"),
        jev_model=os.environ.get("JEV_MODEL", "~typesafe/jev-latest"),
        decisions_url=base_url + "/decisions",
    )
    # Не создаём LLM-клиент без ключа: API отвечает 503 при запросе.
    planner = LlmPlanner(settings) if settings.routerai_api_key else MissingPlanner()
    return PipelineTripGenerator(documents, planner, JevSelector(settings), OsrmRouter(
        os.environ.get("OSRM_BASE_URL", "http://127.0.0.1:5000")))


class MissingPlanner:
    async def plan(self, user_query, city, available_categories):
        raise RuntimeError("LLM не настроена: задайте ROUTERAI_API_KEY в .env")