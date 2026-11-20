"""Загрузка нормализованных документов из файла или папки JSON."""

import json
from pathlib import Path

from app.backend.domain.models import Place, SearchDocument


def load_places(path: Path) -> list[Place | SearchDocument]:
    if path.is_dir():
        files = sorted(path.glob("*.json"))
        if not files:
            raise ValueError("В папке корпуса нет JSON-документов")
    else:
        files = [path]
    places: list[Place | SearchDocument] = []
    ids: set[str] = set()
    for file in files:
        rows = json.loads(file.read_text(encoding="utf-8"))
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            raise ValueError(f"{file.name}: нужен JSON-объект или массив документов")
        for position, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ValueError(f"{file.name}, документ {position}: нужен JSON-объект")
            try:
                if "places" in row:
                    fields = dict(row)
                    members = fields.pop("places")
                    if not isinstance(members, list):
                        raise ValueError("places: нужен массив")
                    member_places = tuple(Place(**p) for p in members)
                    if "text" not in fields:
                        fields["text"] = "\n\n".join(p.text for p in member_places)
                    place = SearchDocument(**fields, places=member_places)
                else:
                    place = Place(**row)
            except (TypeError, ValueError) as error:
                raise ValueError(f"{file.name}, документ {position}: {error}") from error
            if place.id in ids:
                raise ValueError(f"Повтор ID документа: {place.id}")
            ids.add(place.id)
            places.append(place)
    return places
