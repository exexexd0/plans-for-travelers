import type { IconName } from './ui';
import { requestTrip, type ApiTrip } from './api';

export type Step = 'city' | 'interests' | 'prompt' | 'duration' | 'review' | 'generating' | 'trip' | 'route';

export interface Plan {
  city: string;
  interests: string[];
  days: number;
  /** yyyy-mm-dd, local date */
  start: string;
  prompt?: string | null;
}

export interface Interest {
  id: string;
  label: string;
  icon: IconName;
}

export const CITIES = ['Иваново', 'Москва', 'Калининград', 'Казань', 'Сочи', 'Санкт-Петербург'];
export const AVAILABLE_CITIES = CITIES.slice(0, 2);

export const INTERESTS: Interest[] = [
  { id: 'kids', label: 'Прогулка с детьми', icon: 'kids' },
  { id: 'food', label: 'Кафе и еда по пути', icon: 'coffee' },
  { id: 'nature', label: 'Природа и парки', icon: 'tree' },
  { id: 'buildings', label: 'Красивые здания', icon: 'landmark' },
  { id: 'art', label: 'Выставки и галереи', icon: 'image' },
  { id: 'active', label: 'Активный отдых', icon: 'mountain' },
  { id: 'unusual', label: 'Необычные места', icon: 'sparkles' },
];

export const DURATIONS = [1, 2, 3, 4, 5, 6, 7];

export const durationLabel = (days: number) => (days === 1 ? '1 день' : `до ${days} дней`);

// ---------- dates ----------

const MONTHS_SHORT = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
const MONTHS_LONG = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
];
const WEEKDAYS = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];

export function toISO(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${m}-${day}`;
}

export function fromISO(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
}

export const todayISO = () => toISO(new Date());

export function addDays(iso: string, n: number): Date {
  const d = fromISO(iso);
  d.setDate(d.getDate() + n);
  return d;
}

/** «9 — 10 окт 2026», «30 окт — 2 ноя 2026», «9 окт 2026» */
export function formatRange(start: string, days: number): string {
  const a = fromISO(start);
  const b = addDays(start, days - 1);
  const tail = `${MONTHS_SHORT[b.getMonth()]} ${b.getFullYear()}`;
  if (days === 1) return `${a.getDate()} ${tail}`;
  if (a.getMonth() === b.getMonth() && a.getFullYear() === b.getFullYear()) {
    return `${a.getDate()} — ${b.getDate()} ${tail}`;
  }
  const head =
    a.getFullYear() === b.getFullYear()
      ? `${a.getDate()} ${MONTHS_SHORT[a.getMonth()]}`
      : `${a.getDate()} ${MONTHS_SHORT[a.getMonth()]} ${a.getFullYear()}`;
  return `${head} — ${b.getDate()} ${tail}`;
}

/** «пт, 9 окт» */
export const formatDay = (d: Date) => `${WEEKDAYS[d.getDay()]}, ${d.getDate()} ${MONTHS_SHORT[d.getMonth()]}`;

/** «пт, 9 октября» */
export const formatDayLong = (d: Date) => `${WEEKDAYS[d.getDay()]}, ${d.getDate()} ${MONTHS_LONG[d.getMonth()]}`;

/** «9 октября» */
export const formatLong = (d: Date) => `${d.getDate()} ${MONTHS_LONG[d.getMonth()]}`;

export function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

// ---------- маршрут из API ----------

export interface Stop {
  id: string;
  name: string;
  photo: string | null;
  address: string | null;
  description: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface RouteDay {
  date: Date;
  title: string;
  summary: string;
  cover: string | null;
  stops: Stop[];
  geometry: [number, number][] | null;
}

export interface Trip {
  city: string;
  description: string;
  cover: string | null;
  days: RouteDay[];
}

export async function buildRoute(plan: Plan, signal?: AbortSignal): Promise<Trip> {
  const response: ApiTrip = await requestTrip(plan, plan.prompt, signal);
  return {
    city: response.city,
    description: response.description,
    cover: response.image_url ?? null,
    days: response.days.map((day) => ({
      date: fromISO(day.date),
      title: day.title,
      summary: day.summary,
      cover: day.image_url ?? null,
      geometry: day.route?.geometry.coordinates ?? null,
      stops: day.stops.map((stop) => ({
        id: stop.id, name: stop.name, photo: stop.image_url ?? null, address: stop.address ?? null, description: stop.description ?? null,
        latitude: stop.latitude, longitude: stop.longitude,
      })),
    })),
  };
}