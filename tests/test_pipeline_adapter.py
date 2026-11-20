from datetime import date

import pytest

from app.backend.api.schemas import TripRequest
from app.backend.pipeline_adapter import PipelineTripGenerator, decode_polyline, pipeline_query


def test_decode_osrm_polyline_in_geojson_order():
    assert decode_polyline('_p~iF~ps|U_ulLnnqC_mqNvxq`@') == [
        (-120.2, 38.5), (-120.95, 40.7), (-126.453, 43.252),
    ]
    with pytest.raises(ValueError):
        decode_polyline('_')


@pytest.mark.asyncio
async def test_repeats_one_generated_day_and_preserves_waypoint_order():
    calls = []
    async def run_day(request):
        calls.append(request)
        return {
            'route_title': 'Прогулка',
            'steps': [
                {'primary': {'org_id': 'a', 'address': 'Адрес A', 'type': 'Музей'}, 'backup': None},
                {'primary': {'org_id': 'b', 'address': 'Адрес B'}, 'backup': {'org_id': 'c', 'address': 'Адрес C', 'type': 'Парк'}},
            ],
            'waypoints': [
                {'place_id': 'c', 'name': 'Запасное место', 'lat': 57, 'lon': 40},
                {'place_id': 'a', 'name': 'Первое место', 'lat': 57.1, 'lon': 40.1},
            ],
            'route_geometry': '_p~iF~ps|U_ulLnnqC_mqNvxq`@',
        }

    request = TripRequest(city='Иваново', interests=['food', 'buildings'], days=7,
                          start=date(2099, 12, 29), prompt='Без спешки')
    trip = await PipelineTripGenerator(run_day).generate(request)
    assert len(calls) == 1
    assert 'Кафе и еда по пути' in pipeline_query(request)
    assert 'Красивые здания' in pipeline_query(request)
    assert 'Без спешки' in pipeline_query(request)
    assert len(trip.days) == 7
    assert trip.days[-1].date == date(2100, 1, 4)
    assert [stop.id for stop in trip.days[0].stops] == ['c', 'a']
    assert [stop.address for stop in trip.days[0].stops] == ['Адрес C', 'Адрес A']
    assert [stop.description for stop in trip.days[0].stops] == ['Парк', 'Музей']
    assert all(day.stops == trip.days[0].stops and day.route == trip.days[0].route for day in trip.days)
    assert all(day.image_url is None for day in trip.days)


@pytest.mark.asyncio
async def test_rejects_waypoint_absent_from_selected_candidates():
    async def run_day(_):
        return {'route_title': 'Маршрут', 'steps': [], 'waypoints': [{'place_id': 'missing'}]}
    request = TripRequest(city='Иваново', interests=['food'], days=1, start=date(2099, 1, 1))
    with pytest.raises(ValueError, match='неизвестное место'):
        await PipelineTripGenerator(run_day).generate(request)


def test_public_place_retains_original_type():
    from app.pipeline.rag.graph import public_place

    assert public_place({"org_id": "1", "type": "Торговый центр"})["type"] == "Торговый центр"