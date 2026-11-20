"""Однодневная цепочка с настоящим BM25 и тестовыми HTTP-ответами LLM/OSRM."""

import json
from datetime import date

import httpx
import pytest

from app.backend.api.schemas import TripRequest
from app.backend.domain.models import Place, SearchDocument
from app.backend.infrastructure.llm.client import LlmSelector
from app.backend.main import create_app
from app.backend.pipeline_adapter import PipelineTripGenerator, decode_polyline
from app.pipeline.rag.routing import OsrmRouter


def documents():
    rows = [
        ("D01", "p1", "музей", 43.252, -126.453),
        ("D02", "p2", "кофе", 40.7, -120.95),
        ("D03", "p3", "парк", 38.5, -120.2),
        ("D04", "p4", "театр", 57, 41),
    ]
    return [SearchDocument(id=doc, name=word, city="Иваново", text=word,
                          category=word, places=(Place(
                              id=id, name=word, city="Иваново", text=word,
                              lat=lat, lon=lon, address="Адрес " + id, category=word),))
            for doc, id, word, lat, lon in rows]


def request_data():
    return {"city": "Иваново", "interests": ["food"], "days": 1,
            "start": date.today().isoformat(), "prompt": "музей кофе парк"}


def test_decode_osrm_polyline_in_geojson_order():
    assert decode_polyline('_p~iF~ps|U_ulLnnqC_mqNvxq`@') == [
        (-120.2, 38.5), (-120.95, 40.7), (-126.453, 43.252),
    ]
    with pytest.raises(ValueError):
        decode_polyline('_')


@pytest.mark.asyncio
async def test_api_bm25_llm_osrm_use_only_three_documents_and_source_coordinates():
    calls = []

    def respond(request):
        calls.append(request)
        if request.url.host == "llm.test":
            payload = json.loads(request.content)
            context = json.loads(payload["messages"][1]["content"])
            assert {d["id"] for d in context["documents"]} == {"D01", "D02", "D03"}
            assert "музей кофе парк" in context["query"]
            assert context["date"] == date.today().isoformat()
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
                "title": "Парк и музей", "place_ids": ["p3", "p1"], "insufficient_places": True,
            })}}]})
        assert request.url.host == "osrm.test"
        assert request.url.path == "/route/v1/foot/-120.2,38.5;-126.453,43.252"
        return httpx.Response(200, json={"code": "Ok", "routes": [{
            "distance": 100, "duration": 10,
            "geometry": '_p~iF~ps|U_ulLnnqC_mqNvxq`@',
            "legs": [{"duration": 10, "distance": 100}],
        }]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as external:
        generator = PipelineTripGenerator(documents(),
            LlmSelector("test-key", "https://llm.test", "test-model", external),
            OsrmRouter("https://osrm.test", external))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(generator)),
                                     base_url="http://test") as api:
            response = await api.post("/api/v1/trips/generate", json=request_data())
    assert response.status_code == 200
    trip = response.json()
    assert len(trip["days"]) == 1
    day = trip["days"][0]
    assert [p["id"] for p in day["stops"]] == ["p3", "p1"]
    assert day["stops"][0]["latitude"] == 38.5
    assert day["stops"][0]["name"] == "парк"
    assert day["stops"][0]["address"] == "Адрес p3"
    assert "Тестовый режим, мест пока не много" in day["summary"]
    assert day["route"]["geometry"]["coordinates"][0] == [-120.2, 38.5]
    assert len(calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("ids", [["p4"], ["p1", "p1"]])
async def test_rejects_ids_outside_retrieved_documents_and_duplicates(ids):
    def respond(request):
        assert request.url.host == "llm.test", "OSRM must not receive invalid places"
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "title": "Маршрут", "place_ids": ids,
        })}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as external:
        generator = PipelineTripGenerator(documents(),
            LlmSelector("key", "https://llm.test", "model", external),
            OsrmRouter("https://osrm.test", external))
        with pytest.raises(ValueError):
            await generator.generate(TripRequest(**request_data()))


@pytest.mark.asyncio
async def test_unknown_city_is_rejected_before_external_calls():
    def unexpected(request):
        pytest.fail("External calls are not allowed for an unknown city")
    async with httpx.AsyncClient(transport=httpx.MockTransport(unexpected)) as external:
        generator = PipelineTripGenerator(documents(),
            LlmSelector("key", "https://llm.test", "model", external),
            OsrmRouter("https://osrm.test", external))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(generator)),
                                     base_url="http://test") as api:
            response = await api.post("/api/v1/trips/generate", json={**request_data(), "city": "Москва"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_single_place_needs_no_osrm_and_missing_key_returns_503():
    def respond(request):
        assert request.url.host == "llm.test"
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "title": "Музей", "place_ids": ["p1"],
        })}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as external:
        generator = PipelineTripGenerator(documents(),
            LlmSelector("key", "https://llm.test", "model", external),
            OsrmRouter("https://osrm.test", external))
        trip = await generator.generate(TripRequest(**request_data()))
        assert trip.days[0].route is None
        generator.selector.api_key = ""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(generator)),
                                     base_url="http://test") as api:
            assert (await api.post("/api/v1/trips/generate", json=request_data())).status_code == 503
