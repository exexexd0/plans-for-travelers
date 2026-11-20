import type { Plan } from './state';

export interface ApiStop {
  id: string;
  name: string;
  address?: string | null;
  description?: string | null;
  image_url?: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface ApiDay {
  date: string;
  title: string;
  summary: string;
  image_url?: string | null;
  stops: ApiStop[];
  route: { geometry: { type: 'LineString'; coordinates: [number, number][] } } | null;
}

export interface ApiTrip {
  city: string;
  description: string;
  image_url?: string | null;
  days: ApiDay[];
}

/** Запрос к API; получение маршрута приложением остаётся за buildRoute. */
export async function requestTrip(plan: Plan, prompt?: string | null, signal?: AbortSignal): Promise<ApiTrip> {
  const response = await fetch('/api/v1/trips/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...plan, ...(prompt === undefined ? {} : { prompt }) }),
    signal,
  });
  if (!response.ok) throw new Error('Не удалось построить маршрут. Попробуйте ещё раз.');
  const value: unknown = await response.json();
  if (!isTrip(value, plan)) throw new Error('Сервер вернул некорректный маршрут.');
  return value;
}

function isTrip(value: unknown, plan: Plan): value is ApiTrip {
  if (!value || typeof value !== 'object') return false;
  const trip = value as ApiTrip;
  if (typeof trip.city !== 'string' || typeof trip.description !== 'string' || !validImage(trip.image_url)
      || !Array.isArray(trip.days) || trip.days.length !== plan.days) return false;
  const [year, month, date] = plan.start.split('-').map(Number);
  return trip.days.every((day, index) => {
    const expected = new Date(Date.UTC(year, month - 1, date + index)).toISOString().slice(0, 10);
    if (!day || day.date !== expected || typeof day.title !== 'string' || typeof day.summary !== 'string'
        || !validImage(day.image_url) || !Array.isArray(day.stops)) return false;
    if (!day.stops.every((stop) => stop && typeof stop.id === 'string' && !!stop.id
      && typeof stop.name === 'string' && !!stop.name && (stop.address == null || typeof stop.address === 'string')
      && (stop.description == null || typeof stop.description === 'string') && validImage(stop.image_url)
      && ((stop.latitude === null && stop.longitude === null)
        || (typeof stop.latitude === 'number' && Number.isFinite(stop.latitude) && Math.abs(stop.latitude) <= 90
          && typeof stop.longitude === 'number' && Number.isFinite(stop.longitude) && Math.abs(stop.longitude) <= 180)))) return false;
    if (day.route === null) return true;
    const geometry = day.route?.geometry;
    return !!geometry && geometry.type === 'LineString' && Array.isArray(geometry.coordinates)
      && geometry.coordinates.length >= 2 && geometry.coordinates.every((point) => Array.isArray(point)
        && point.length === 2 && point.every((coordinate) => typeof coordinate === 'number' && Number.isFinite(coordinate))
        && Math.abs(point[0]) <= 180 && Math.abs(point[1]) <= 90);
  });
}

function validImage(value: unknown): boolean {
  if (value == null) return true;
  if (typeof value !== 'string') return false;
  try { return ['http:', 'https:'].includes(new URL(value).protocol); } catch { return false; }
}
