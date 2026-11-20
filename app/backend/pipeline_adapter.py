"""Временный адаптер однодневного пайплайна для API поездок."""

import asyncio
from datetime import timedelta
from typing import Awaitable, Callable

from fastapi import HTTPException

from app.backend.api.schemas import DayRoute, LineString, RouteDay, Stop, TripRequest, TripResponse
from app.pipeline.rag.graph import build_route_graph, initial_state, route_view, validate_route
from app.pipeline.rag.jev import JevSelector
from app.pipeline.rag.planner import LlmPlanner
from app.pipeline.rag.routing import OsrmRouter
from app.pipeline.rag.settings import load_settings
from app.pipeline.rag.store import available_categories, open_store

# Эти названия соответствуют текущим подписям интересов во фронтенде.
INTEREST_LABELS = {
    "kids": "Прогулка с детьми",
    "food": "Кафе и еда по пути",
    "nature": "Природа и парки",
    "buildings": "Красивые здания",
    "art": "Выставки и галереи",
    "active": "Активный отдых",
    "unusual": "Необычные места",
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


async def run_pipeline(request: TripRequest) -> dict:
    settings = load_settings()
    if request.city.strip().casefold() != settings.city.strip().casefold():
        raise HTTPException(status_code=422, detail="Для выбранного города нет данных.")
    categories = await asyncio.to_thread(available_categories, settings)
    store = await open_store(settings)
    try:
        graph = build_route_graph(LlmPlanner(settings), store, JevSelector(settings), router=OsrmRouter(settings.osrm_base_url))
        state = await graph.ainvoke(initial_state(pipeline_query(request), settings.city, categories))
        route = route_view(state)
        validate_route(route)
        return route
    finally:
        await store.close()


class PipelineTripGenerator:
    def __init__(self, run_day: Callable[[TripRequest], Awaitable[dict]] = run_pipeline):
        self.run_day = run_day

    async def generate(self, request: TripRequest) -> TripResponse:
        result = await self.run_day(request)
        if result.get("stopped_reason") or not result.get("waypoints"):
            raise ValueError("Пайплайн не вернул места маршрута")
        sources = {
            place["org_id"]
            for step in result.get("steps", [])
            for place in (step.get("primary"), step.get("backup"))
            if place and place.get("org_id")
        }
        points = result["waypoints"]
        if any(not point.get("place_id") or point["place_id"] not in sources for point in points):
            raise ValueError("Маршрут содержит неизвестное место")
        if len({point["place_id"] for point in points}) != len(points):
            raise ValueError("В одном дне есть повторяющиеся места")
        stops = [Stop(id=str(point["place_id"]), name=point["name"], latitude=point["lat"],
                      longitude=point["lon"], image_url=None) for point in points]
        geometry = decode_polyline(result.get("route_geometry") or "")
        route = DayRoute(geometry=LineString(coordinates=geometry)) if len(geometry) >= 2 else None
        title = (result.get("route_title") or "").strip()
        if not title:
            raise ValueError("Пайплайн не вернул название маршрута")
        summary = "Места: " + ", ".join(stop.name for stop in stops) + "."
        days = [RouteDay(date=request.start + timedelta(days=index), title=title, summary=summary,
                         image_url=None, stops=stops, route=route) for index in range(request.days)]
        description = title if request.days == 1 else title + ". Маршрут первого дня повторяется в остальные дни."
        return TripResponse(city=request.city, description=description, image_url=None, days=days)


def create_pipeline_generator() -> PipelineTripGenerator:
    return PipelineTripGenerator()
