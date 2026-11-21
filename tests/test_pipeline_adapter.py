from datetime import date
from pathlib import Path

import httpx
import pytest

from app.backend.api.schemas import TripRequest
from app.backend.infrastructure.corpus.loader import load_places
from app.backend.main import create_app
from app.backend.pipeline_adapter import PipelineTripGenerator, decode_polyline
from app.pipeline.rag.models import CategoryOrder, RoutePlan
from app.pipeline.rag.planner import PlannerTimeout


CORPUS = Path(__file__).resolve().parents[1] / "app/backend/data/ivanovo"


def request_data():
    return {"city": "Иваново", "interests": ["food", "buildings"], "days": 1,
            "start": date.today().isoformat(), "prompt": "Сначала здания, потом еда"}


class Planner:
    async def plan(self, user_query, city, available_categories):
        assert "Красивые здания" in user_query
        return RoutePlan(route_title="Прогулка", required_points=["food", "sight"],
                         precedence=[CategoryOrder(before="sight", after="food")])


class Selector:
    def __init__(self):
        self.calls = []

    async def choose(self, *, category, candidates, route_so_far, **kwargs):
        self.calls.append((category, candidates, list(route_so_far)))
        return (candidates[0], candidates[1] if len(candidates) > 1 else None, "test") if candidates else (None, None, "empty")


class Router:
    def __init__(self):
        self.routed = []

    async def table(self, places, profile):
        assert profile == "foot"
        n = len(places)
        matrix = [[0 if i == j else 100 for j in range(n)] for i in range(n)]
        return matrix, matrix

    async def route(self, places, profile):
        from types import SimpleNamespace
        self.routed = places
        return SimpleNamespace(geometry='_p~iF~ps|U_ulLnnqC_mqNvxq`@', distance=100,
                               duration=10, legs=[SimpleNamespace(duration=10, distance=100)] * (len(places)-1))


def test_decode_osrm_polyline_in_geojson_order():
    assert decode_polyline('_p~iF~ps|U_ulLnnqC_mqNvxq`@') == [
        (-120.2, 38.5), (-120.95, 40.7), (-126.453, 43.252),
    ]
    with pytest.raises(ValueError):
        decode_polyline('_')


@pytest.mark.asyncio
async def test_bm25_per_goal_selects_found_places_and_respects_order():
    selector, router = Selector(), Router()
    generator = PipelineTripGenerator(load_places(CORPUS), Planner(), selector, router)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(generator)), base_url="http://test") as api:
        response = await api.post("/api/v1/trips/generate", json=request_data())
    assert response.status_code == 200, response.text
    assert [call[0] for call in selector.calls] == ["food", "sight"]
    assert all(call[1] for call in selector.calls)
    assert selector.calls[1][2][0]["primary"]["org_id"] == selector.calls[0][1][0]["org_id"]
    assert all(candidate["document_id"] and candidate["text"] for _, candidates, _ in selector.calls for candidate in candidates)
    assert [p["category"] for p in router.routed] == ["sight", "food"]
    stops = response.json()["days"][0]["stops"]
    assert [p["id"] for p in stops] == [p["org_id"] for p in router.routed]
    assert all(p["description"] for p in stops)


@pytest.mark.asyncio
async def test_empty_goal_reports_missing_without_replacing_it():
    class MissingPlanner:
        async def plan(self, user_query, city, available_categories):
            return RoutePlan(route_title="Прогулка", required_points=["food", "station"])
    selector = Selector()
    generator = PipelineTripGenerator(load_places(CORPUS), MissingPlanner(), selector, Router())
    trip = await generator.generate(TripRequest(**{**request_data(), "interests": ["food"]}))
    assert selector.calls[1][0] == "station" and not selector.calls[1][1]
    assert len(trip.days[0].stops) == 1
    assert "Тестовый режим, мест пока не много" in trip.description


@pytest.mark.asyncio
async def test_rejects_selector_id_outside_bm25_candidates():
    class BadSelector:
        async def choose(self, **kwargs):
            return {"org_id": "not-in-corpus"}, None, "test"
    generator = PipelineTripGenerator(load_places(CORPUS), Planner(), BadSelector(), Router())
    with pytest.raises(ValueError, match="вне результатов BM25"):
        await generator.generate(TripRequest(**request_data()))


@pytest.mark.asyncio
async def test_unknown_city_and_planner_timeout():
    generator = PipelineTripGenerator(load_places(CORPUS), Planner(), Selector(), Router())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(generator)), base_url="http://test") as api:
        response = await api.post("/api/v1/trips/generate", json={**request_data(), "city": "Москва"})
        assert response.status_code == 422
        class TimedOutPlanner:
            async def plan(self, *args):
                raise PlannerTimeout("timeout")
        generator.planner = TimedOutPlanner()
        assert (await api.post("/api/v1/trips/generate", json=request_data())).status_code == 503

@pytest.mark.asyncio
async def test_explicit_food_and_buildings_are_not_lost_when_planner_omits_one():
    class OmittingPlanner:
        async def plan(self, user_query, city, available_categories):
            return RoutePlan(route_title="Прогулка", required_points=["food"])
    selector, router = Selector(), Router()
    trip = await PipelineTripGenerator(load_places(CORPUS), OmittingPlanner(), selector, router).generate(
        TripRequest(**request_data()))
    assert [call[0] for call in selector.calls] == ["food", "sight"]
    assert len(trip.days[0].stops) == 2

@pytest.mark.asyncio
async def test_bm25_candidates_account_for_user_wishes():
    from app.backend.bm25_route_retriever import BM25RouteRetriever
    from app.backend.domain.models import Place, SearchDocument
    from app.backend.infrastructure.search.bm25 import BM25Search

    places = [
        Place(id="a", name="Кафе А", city="Иваново", text="кафе пироги", category="Кафе", lat=57, lon=40),
        Place(id="b", name="Кафе Б", city="Иваново", text="кафе суп", category="Кафе", lat=57, lon=40),
    ]
    docs = [SearchDocument(id=f"D{i}", name=place.name, city=place.city, text=place.text,
                           category=place.category, places=(place,)) for i, place in enumerate(places)]
    retriever = BM25RouteRetriever(docs, BM25Search(docs))
    candidates = await retriever.search(user_query="хочу суп", city="Иваново", category="food", excluded_org_ids=[])
    assert candidates[0]["org_id"] == "b"
    assert candidates[0]["document_id"] == "D1"
