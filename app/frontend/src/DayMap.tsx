import type { RouteDay } from './state';
import { Icon, img } from './ui';

// условная схема: три набора точек, чтобы соседние дни выглядели по-разному
const SCHEMES: [number, number][][] = [
  [[52, 236], [112, 170], [190, 196], [250, 120], [150, 70]],
  [[60, 90], [130, 130], [100, 210], [200, 235], [270, 160]],
  [[280, 230], [210, 170], [250, 95], [150, 110], [70, 160]],
];

/** плавная линия через точки (Catmull-Rom → кубические кривые) */
function smooth(pts: [number, number][]): string {
  let d = `M${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(i - 1, 0)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(i + 2, pts.length - 1)];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    d += `C${c1[0]} ${c1[1]} ${c2[0]} ${c2[1]} ${p2[0]} ${p2[1]}`;
  }
  return d;
}

/** Карта одного дня: линия идёт только через места этого дня, номера совпадают со списком. */
export function DayMap({ day, index }: { day: RouteDay; index: number }) {
  const real = day.map;
  const width = real?.width ?? 342;
  const height = real?.height ?? 220;
  const points = real?.points ?? SCHEMES[index % SCHEMES.length].slice(0, day.stops.length);
  const path = real?.path ?? smooth(points);
  // схема нарисована в поле 342×320, показываем его среднюю полосу
  const viewBox = real ? `0 0 ${width} ${height}` : `0 45 ${width} ${height}`;

  return (
    <div className="map" style={{ aspectRatio: `${width} / ${height}` }}>
      {real && <img src={img(real.image)} alt="" />}
      <svg viewBox={viewBox} preserveAspectRatio="xMidYMid slice" fill="none" role="img" aria-label={`Карта дня ${index + 1}`}>
        {!real && (
          <>
            <rect width="342" height="320" fill="#F3F1E4" />
            <path d="M-10 60 C 60 20, 150 40, 200 10 L 360 -10 L 360 150 C 300 190, 220 130, 150 150 S 40 200, -10 170 Z" fill="#CFE3C4" fillOpacity="0.85" />
            <path d="M-10 250 C 60 220, 130 270, 210 240 S 320 230, 360 260 L 360 330 L -10 330 Z" fill="#D9E8C6" fillOpacity="0.9" />
            <path d="M-10 196 C 60 216, 120 176, 190 190 S 300 230, 360 200" stroke="#BCD9EC" strokeWidth="20" strokeLinecap="round" />
            <ellipse cx="282" cy="62" rx="40" ry="24" fill="#BCD9EC" />
            <g stroke="#fff" strokeOpacity="0.9" strokeWidth="3" strokeLinecap="round">
              <path d="M-10 120 C 80 140, 160 100, 360 150" />
              <path d="M90 -10 C 100 100, 140 200, 120 330" />
              <path d="M230 -10 C 220 110, 260 220, 250 330" />
            </g>
          </>
        )}
        <path d={path} stroke="#4E9A6B" strokeOpacity="0.3" strokeWidth="9" strokeLinecap="round" strokeLinejoin="round" />
        <path d={path} stroke="#357A52" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        {points.map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="13" fill="#fff" stroke="#357A52" strokeWidth="2" />
            <text x={x} y={y + 4} textAnchor="middle" className="map__num">
              {i + 1}
            </text>
          </g>
        ))}
      </svg>
      <span className="map__compass" aria-hidden="true">
        <Icon name="compass" />
      </span>
      {real && <span className="map__credit">{real.credit}</span>}
    </div>
  );
}
