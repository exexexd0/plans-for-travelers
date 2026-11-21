"""Сквозная проверка HTTP API с тестовым генератором без внешних сервисов."""

import socket
import threading
import time
from datetime import date

import httpx
import uvicorn

from app.backend.main import create_app


class FixtureGenerator:
    def __init__(self):
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        return {
            "city": request.city,
            "description": "Маршрут для проверки",
            "days": [
                {
                    "date": request.start,
                    "title": f"День {index + 1}",
                    "summary": "Проверочное место",
                    "stops": [{"id": str(index), "name": "Место", "latitude": 57, "longitude": 40,
                               "image_url": "https://example.org/photo.jpg"}],
                    "route": None,
                }
                for index in range(request.days)
            ],
        }


def test_http_roundtrip_with_optional_prompt_and_one_day():
    generator = FixtureGenerator()
    app = create_app(generator)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(16)
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert server.started, "HTTP-сервер не запустился"
            url = f"http://127.0.0.1:{port}/api/v1/trips/generate"
            start = date.today().isoformat()
            request = {"city": "Иваново", "interests": ["food"], "days": 1, "start": start,
                       "prompt": "Без спешки"}
            response = httpx.post(url, json=request, timeout=5)
            assert response.status_code == 200
            trip = response.json()
            assert generator.requests[-1].prompt == "Без спешки"
            assert len(trip["days"]) == 1
            assert trip["days"][-1]["date"] == start
            assert trip["image_url"] == trip["days"][0]["stops"][0]["image_url"]
            del request["prompt"]
            request["days"] = 1
            assert httpx.post(url, json=request, timeout=5).status_code == 200
            assert generator.requests[-1].prompt is None
        finally:
            server.should_exit = True
            thread.join(timeout=5)
            assert not thread.is_alive()


def test_uvicorn_loads_factory_from_environment(tmp_path):
    import os
    import subprocess
    import sys

    module = tmp_path / "example_generator.py"
    module.write_text(
        "class Generator:\n"
        "    async def generate(self, request):\n"
        "        return {'city': request.city, 'description': request.prompt or '', "
        "'days': [{'date': request.start, 'title': 'День', 'summary': '', 'stops': [], 'route': None}]}\n"
        "def create():\n"
        "    return Generator()\n",
        encoding="utf-8",
    )
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = os.environ.copy()
    env["TRIP_GENERATOR_FACTORY"] = "example_generator:create"
    env["PYTHONPATH"] = os.pathsep.join((str(tmp_path), os.getcwd()))
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.backend.main:app", "--host", "127.0.0.1", "--port", str(port)],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        url = f"http://127.0.0.1:{port}/api/v1/trips/generate"
        request = {"city": "Иваново", "interests": ["food"], "days": 1,
                   "start": date.today().isoformat(), "prompt": "Без спешки"}
        deadline = time.monotonic() + 10
        response = None
        while time.monotonic() < deadline and process.poll() is None:
            try:
                response = httpx.post(url, json=request, timeout=1)
                break
            except httpx.ConnectError:
                time.sleep(0.05)
        assert response is not None, "Сервер с настроенной фабрикой не запустился"
        assert response.status_code == 200
        assert response.json()["description"] == request["prompt"]
    finally:
        process.terminate()
        process.wait(timeout=5)
