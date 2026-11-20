"""HTTP API; реализация генератора подключается через зависимость FastAPI."""

import importlib
import inspect
import logging
import os
from datetime import timedelta
from typing import Protocol

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.backend.api.schemas import TripRequest, TripResponse

logger = logging.getLogger(__name__)


class TripGenerator(Protocol):
    async def generate(self, request: TripRequest) -> TripResponse: ...


def get_trip_generator(request: Request) -> TripGenerator | None:
    generator = getattr(request.app.state, "trip_generator", None)
    return generator


def create_app(generator: TripGenerator | None = None) -> FastAPI:
    app = FastAPI(title="API маршрутов")
    app.state.trip_generator = generator

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _error: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "Проверьте данные поездки."})

    @app.post("/api/v1/trips/generate", response_model=TripResponse)
    async def generate_trip(
        data: TripRequest,
        trip_generator: TripGenerator | None = Depends(get_trip_generator),
    ) -> TripResponse:
        if trip_generator is None:
            raise HTTPException(status_code=503, detail="Генерация маршрутов пока недоступна.")
        try:
            result = TripResponse.model_validate(await trip_generator.generate(data))
            if len(result.days) != data.days or any(
                day.date != data.start + timedelta(days=i) for i, day in enumerate(result.days)
            ):
                raise ValueError("Число или даты дней не соответствуют запросу")
            return result
        except HTTPException:
            raise
        except (ValidationError, ValueError):
            logger.exception("Генератор вернул некорректную поездку")
            raise HTTPException(status_code=502, detail="Не удалось получить корректный маршрут.") from None
        except Exception:
            logger.exception("Ошибка генерации поездки")
            raise HTTPException(status_code=503, detail="Не удалось построить маршрут. Попробуйте ещё раз.") from None

    return app


def load_configured_generator() -> TripGenerator | None:
    """Загрузить явно настроенную фабрику генератора; без неё API недоступен."""
    reference = os.environ.get("TRIP_GENERATOR_FACTORY", "").strip()
    if not reference:
        return None
    module_name, separator, factory_name = reference.partition(":")
    if not separator or not module_name or not factory_name or ":" in factory_name:
        raise ValueError("TRIP_GENERATOR_FACTORY должен иметь формат модуль:фабрика")
    factory = getattr(importlib.import_module(module_name), factory_name)
    if not callable(factory):
        raise TypeError("Фабрика генератора должна быть вызываемой")
    generator = factory()
    if not inspect.iscoroutinefunction(getattr(generator, "generate", None)):
        raise TypeError("Генератор должен предоставлять асинхронный метод generate")
    return generator


from app.backend.pipeline_adapter import create_pipeline_generator

app = create_app(load_configured_generator() or create_pipeline_generator())
