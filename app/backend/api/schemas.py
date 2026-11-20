"""Схемы согласованного HTTP-контракта поездки."""

from datetime import date
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


def _http_image(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError("Адрес изображения должен быть абсолютным HTTP(S) URL")
    return value


ImageUrl = Annotated[str, AfterValidator(_http_image)]
Interest = Literal["kids", "food", "nature", "buildings", "art", "active", "unusual"]


class TripRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    city: str = Field(min_length=1)
    interests: list[Interest] = Field(min_length=1)
    days: int = Field(ge=1, le=7, strict=True)
    start: date
    prompt: str | None = None

    @model_validator(mode="after")
    def start_is_not_in_the_past(self):
        if self.start < date.today():
            raise ValueError("Дата начала не может быть в прошлом")
        return self


class Stop(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    address: str | None = None
    description: str | None = None
    image_url: ImageUrl | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def coordinates_are_paired(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Координаты должны быть указаны вместе")
        return self


class LineString(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[tuple[float, float]] = Field(min_length=2)


class DayRoute(BaseModel):
    geometry: LineString


class RouteDay(BaseModel):
    date: date
    title: str
    summary: str
    image_url: ImageUrl | None = None
    stops: list[Stop]
    route: DayRoute | None = None

    @model_validator(mode="after")
    def cover_matches_a_stop(self):
        images = [stop.image_url for stop in self.stops if stop.image_url]
        if self.image_url is not None and self.image_url not in images:
            raise ValueError("Изображение дня должно принадлежать месту этого дня")
        if self.image_url is None and images:
            self.image_url = images[0]
        return self


class TripResponse(BaseModel):
    city: str
    description: str
    image_url: ImageUrl | None = None
    days: list[RouteDay]

    @model_validator(mode="after")
    def cover_matches_a_day(self):
        images = [day.image_url for day in self.days if day.image_url]
        if self.image_url is not None and self.image_url not in images:
            raise ValueError("Изображение поездки должно принадлежать одному из её дней")
        if self.image_url is None and images:
            self.image_url = images[0]
        return self
