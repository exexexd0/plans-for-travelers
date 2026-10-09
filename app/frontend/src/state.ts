import type { IconName } from './ui';

export type Step = 'city' | 'interests' | 'duration' | 'review' | 'generating' | 'trip' | 'route';

export interface Plan {
  city: string;
  interests: string[];
  days: number;
  /** yyyy-mm-dd, local date */
  start: string;
}

export interface Interest {
  id: string;
  label: string;
  icon: IconName;
}

export const CITIES = ['Калининград', 'Казань', 'Сочи', 'Санкт-Петербург', 'Москва'];

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

// ---------- route (demo data, no backend yet) ----------

export interface Stop {
  name: string;
  photo: string;
}

/** Готовая карта дня: картинка-подложка и разметка в её пикселях. */
export interface DayMap {
  image: string;
  width: number;
  height: number;
  /** центры точек, по одной на каждое место дня, в том же порядке */
  points: [number, number][];
  /** линия маршрута, атрибут d для <path> */
  path: string;
  credit: string;
}

export interface RouteDay {
  date: Date;
  title: string;
  /** краткий текст о местах дня для карточки на экране «Поездка» */
  summary: string;
  cover: string;
  stops: Stop[];
  /** нет — рисуется условная схема */
  map?: DayMap;
}

const STOPS: Record<string, string[]> = {
  kids: ['Детская площадка в парке', 'Контактный зоопарк', 'Музей занимательных наук'],
  food: ['Кофейня у набережной', 'Рынок с местной едой', 'Ужин с видом на город'],
  nature: ['Городской парк', 'Набережная', 'Ботанический сад', 'Озеро за городом'],
  buildings: ['Исторический центр', 'Старые особняки', 'Главная площадь'],
  art: ['Художественный музей', 'Галерея современного искусства'],
  active: ['Велопрогулка вдоль реки', 'Тропа здоровья'],
  unusual: ['Двор с муралами', 'Смотровая площадка на крыше'],
};

const DAY_TITLES = [
  'Знакомство с городом',
  'Тихие улицы и парки',
  'За город, к воде',
  'Маршрут без спешки',
  'Местные любимые места',
  'Длинная прогулка',
  'Последний день: самое важное',
];

const PHOTOS = ['greenwater', 'water', 'grass', 'flowers', 'canopy', 'pinkgrass', 'lily'];
const COVERS = ['sunforest', 'canopy', 'forestpath', 'field'];
const STOPS_PER_DAY = 5;

/**
 * Демонстрационный первый день для Иванова: реальные места в порядке с севера на юг.
 * Координаты точек и линия сняты с подложки OpenStreetMap (342×320).
 */
const IVANOVO_DAY: Omit<RouteDay, 'date'> = {
  title: 'Музеи и старый центр',
  summary:
    'Вы начнёте у конструктивистского Дома-корабля, посетите музей ивановского ситца и пройдётесь по старинной усадьбе Бурылина, выйдете на площадь Пушкина и закончите день у Щудровской палатки XVII века.',
  cover: 'ivanovo-ship',
  stops: [
    { name: 'Дом-корабль', photo: 'ivanovo-ship' },
    { name: 'Музей ивановского ситца', photo: 'ivanovo-calico' },
    { name: 'Усадьба Бурылина', photo: 'ivanovo-burylin' },
    { name: 'Площадь Пушкина', photo: 'ivanovo-pushkin' },
    { name: 'Щудровская палатка', photo: 'ivanovo-shchudrov' },
  ],
  map: {
    image: 'ivanovo-day1-map',
    width: 342,
    height: 320,
    // музеи ситца и Бурылина стоят через дорогу — точки 2 и 3 немного раздвинуты
    points: [[113, 34], [135, 149], [159, 166], [144, 218], [229, 286]],
    path: 'M113 34L123 34L129 61L131 72L134 81L136 98L138 115L140 128L141 138L144 157L145 181L146 195L146 208L145 218L144 229L145 231L150 236L160 245L165 250L174 261L180 268L184 270L186 269L194 260L197 260L205 266L212 272L215 273L230 279L229 286',
    credit: '© OpenStreetMap',
  },
};

function daySummary(stops: Stop[]): string {
  const names = [...new Set(stops.map((s) => s.name.charAt(0).toLowerCase() + s.name.slice(1)))];
  return `В этот день: ${names.join(', ')}.`;
}

/**
 * Собирает демонстрационный маршрут из выбранных интересов.
 * Реальной генерации пока нет: точки берутся по кругу из заготовок.
 * В каждом дне ровно STOPS_PER_DAY мест — столько же точек на карте дня.
 */
export function buildRoute(plan: Plan): RouteDay[] {
  const ids = plan.interests.length ? plan.interests : Object.keys(STOPS);
  const cursor: Record<string, number> = {};
  let photo = 0;
  const days: RouteDay[] = [];

  for (let d = 0; d < plan.days; d++) {
    const date = addDays(plan.start, d);
    if (d === 0 && plan.city.trim().toLowerCase() === 'иваново') {
      days.push({ ...IVANOVO_DAY, date });
      continue;
    }
    const stops: Stop[] = [];
    for (let i = 0; i < STOPS_PER_DAY; i++) {
      const id = ids[(d * STOPS_PER_DAY + i) % ids.length];
      const pool = STOPS[id];
      const at = cursor[id] ?? 0;
      cursor[id] = at + 1;
      stops.push({ name: pool[at % pool.length], photo: PHOTOS[photo++ % PHOTOS.length] });
    }
    days.push({
      date,
      title: DAY_TITLES[d % DAY_TITLES.length],
      summary: daySummary(stops),
      cover: COVERS[d % COVERS.length],
      stops,
    });
  }
  return days;
}

export function tripDescription(plan: Plan): string {
  const labels = INTERESTS.filter((i) => plan.interests.includes(i.id)).map((i) => i.label.toLowerCase());
  const days = `${plan.days} ${plural(plan.days, 'день', 'дня', 'дней')}`;
  const what = labels.length ? labels.join(', ') : 'главные места города';
  return `Маршрут на ${days}: ${what}. Собран так, чтобы всё успеть без спешки.`;
}
