from datetime import date

import pytest
from pydantic import ValidationError

from app.backend.api.schemas import Stop, TripRequest


def test_request_supports_optional_prompt():
    data = {"city": "Иваново", "interests": ["food"], "days": 2, "start": "2026-12-01"}
    assert TripRequest(**data).prompt is None
    assert TripRequest(**data, prompt="Без спешки").prompt == "Без спешки"
    assert TripRequest(**data).start == date(2026, 12, 1)


def test_request_rejects_unknown_interest_and_duration():
    data = {"city": "Иваново", "interests": ["food"], "days": 2, "start": "2026-12-01"}
    with pytest.raises(ValidationError):
        TripRequest(**{**data, "interests": ["unknown"]})
    with pytest.raises(ValidationError):
        TripRequest(**{**data, "days": 8})


def test_stop_requires_both_coordinates():
    assert Stop(id="1", name="Место").latitude is None
    assert Stop(id="1", name="Место", latitude=57, longitude=40).longitude == 40
    with pytest.raises(ValidationError):
        Stop(id="1", name="Место", latitude=57)


def test_endpoint_passes_prompt_to_generator():
    from fastapi.testclient import TestClient
    from app.backend.main import create_app

    seen = []

    class Generator:
        async def generate(self, request):
            seen.append(request)
            return {
                "city": request.city, "description": "Описание", "image_url": None,
                "days": [{"date": request.start, "title": "День", "summary": "Места",
                          "image_url": None, "stops": [], "route": None}],
            }

    client = TestClient(create_app(Generator()))
    request = {"city": "Иваново", "interests": ["food"], "days": 1,
               "start": "2026-12-01", "prompt": "Без спешки"}
    response = client.post("/api/v1/trips/generate", json=request)
    assert response.status_code == 200
    assert seen[0].prompt == "Без спешки"
    assert response.json()["days"][0]["date"] == request["start"]
    assert client.post("/api/v1/trips/generate", json={**request, "days": 2}).status_code == 502


def test_endpoint_without_generator_is_unavailable():
    from fastapi.testclient import TestClient
    from app.backend.main import create_app

    client = TestClient(create_app())
    request = {"city": "Иваново", "interests": ["food"], "days": 1, "start": "2026-12-01"}
    assert client.post("/api/v1/trips/generate", json=request).status_code == 503
    assert client.post("/api/v1/trips/generate", json={**request, "days": 0}).status_code == 422


def test_images_are_selected_from_stops_and_must_be_http_urls():
    from app.backend.api.schemas import TripResponse

    stop = {"id": "1", "name": "Место", "image_url": "https://example.org/place.jpg"}
    trip = TripResponse.model_validate({
        "city": "Иваново", "description": "Описание", "days": [
            {"date": "2026-12-01", "title": "День", "summary": "Описание", "stops": [stop]}
        ],
    })
    assert trip.days[0].image_url == stop["image_url"]
    assert trip.image_url == stop["image_url"]
    with pytest.raises(ValidationError):
        Stop(id="1", name="Место", image_url="file:///etc/passwd")
    with pytest.raises(ValidationError):
        TripResponse.model_validate({"city": "Иваново", "description": "Описание", "days": [
            {"date": "2026-12-01", "title": "День", "summary": "Описание", "stops": [stop],
             "image_url": "https://example.org/other.jpg"}
        ]})


def test_configured_generator_factory(monkeypatch):
    import types
    from app.backend import main

    class Generator:
        async def generate(self, request):
            return request

    generator = Generator()
    module = types.SimpleNamespace(make=lambda: generator)
    monkeypatch.setattr(main.importlib, "import_module", lambda name: module if name == "example" else None)
    monkeypatch.delenv("TRIP_GENERATOR_FACTORY", raising=False)
    assert main.load_configured_generator() is None
    monkeypatch.setenv("TRIP_GENERATOR_FACTORY", "example:make")
    assert main.load_configured_generator() is generator
    monkeypatch.setenv("TRIP_GENERATOR_FACTORY", "wrong-format")
    with pytest.raises(ValueError):
        main.load_configured_generator()
    monkeypatch.setenv("TRIP_GENERATOR_FACTORY", "example:missing")
    with pytest.raises(AttributeError):
        main.load_configured_generator()
