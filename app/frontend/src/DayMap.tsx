import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { RouteDay } from './state';

/** Интерактивная карта выбранного дня с сохранением порядка мест из списка. */
export function DayMap({ day, placeIndex }: { day: RouteDay; placeIndex?: number }) {
  const container = useRef<HTMLDivElement>(null);
  const hasCoordinates = day.stops.some((stop, index) => (placeIndex === undefined || index === placeIndex)
    && stop.latitude !== null && stop.longitude !== null)
    || (placeIndex === undefined && Boolean(day.geometry?.length));

  useEffect(() => {
    if (!container.current || !hasCoordinates) return;

    const map = L.map(container.current, { zoomControl: true, scrollWheelZoom: true });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    const markerCoordinates: L.LatLngTuple[] = [];
    day.stops.forEach((stop, index) => {
      if ((placeIndex !== undefined && index !== placeIndex) || stop.latitude === null || stop.longitude === null) return;
      const position: L.LatLngTuple = [stop.latitude, stop.longitude];
      markerCoordinates.push(position);
      const icon = L.divIcon({
        className: 'map__pin-wrapper',
        html: `<span class="map__pin">${index + 1}</span>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });
      const popup = document.createElement('span');
      popup.textContent = stop.name;
      L.marker(position, { icon, title: stop.name, alt: `Место ${index + 1}: ${stop.name}` })
        .addTo(map)
        .bindPopup(popup);
    });

    // В GeoJSON сначала идёт долгота, а Leaflet ожидает сначала широту.
    const route: L.LatLngTuple[] = (placeIndex === undefined ? day.geometry ?? [] : []).map(([lon, lat]) => [lat, lon]);
    if (route.length >= 2) {
      L.polyline(route, { color: '#0077ff', weight: 5, opacity: 0.8 }).addTo(map);
    } else if (markerCoordinates.length >= 2) {
      L.polyline(markerCoordinates, { color: '#0077ff', weight: 4, dashArray: '5, 5' }).addTo(map);
    }

    const visiblePoints = [...markerCoordinates, ...route];
    if (visiblePoints.length === 1) {
      map.setView(visiblePoints[0], 16);
    } else {
      map.fitBounds(L.latLngBounds(visiblePoints), { padding: [30, 30], maxZoom: 16 });
    }
    const zoomIn = container.current.querySelector('.leaflet-control-zoom-in');
    const zoomOut = container.current.querySelector('.leaflet-control-zoom-out');
    zoomIn?.setAttribute('aria-label', 'Приблизить карту');
    zoomOut?.setAttribute('aria-label', 'Отдалить карту');
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(container.current);
    return () => {
      observer.disconnect();
      map.remove();
    };
  }, [day, hasCoordinates, placeIndex]);

  if (!hasCoordinates) return <div className="map map--empty glass" role="status">Карта маршрута пока недоступна</div>;
  return <div className="map" ref={container} aria-label={placeIndex === undefined ? "Карта маршрута" : "Карта места"} />;
}
