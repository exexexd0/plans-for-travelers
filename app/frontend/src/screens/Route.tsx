import { useState } from 'react';
import { DayMap } from '../DayMap';
import { formatDayLong, plural, type RouteDay } from '../state';
import { Chip, RoundButton, Screen, Photo } from '../ui';

export function Route({ route, initial = 0, fallback, onBack }: { route: RouteDay[]; initial?: number; fallback: string; onBack: () => void }) {
  const [index, setIndex] = useState(Math.min(initial, route.length - 1));
  const day = route[index];
  const places = day.stops.length;

  return (
    <Screen bg="water" veil={0.7} blur={34}>
      <header className="route__top">
        <RoundButton icon="chevron-left" label="Назад" onClick={onBack} />
        <h1>Маршрут: День {index + 1}</h1>
      </header>

      {route.length > 1 && (
        <div className="chips chips--scroll" role="tablist" aria-label="Дни маршрута">
          {route.map((_, i) => (
            <Chip key={i} active={i === index} role="tab" aria-selected={i === index} onClick={() => setIndex(i)}>
              День {i + 1}
            </Chip>
          ))}
        </div>
      )}

      <section className="guide glass">
        <Photo className="photo guide__photo" url={day.cover} fallback={fallback}>
          <span className="tag">День {index + 1}</span>
        </Photo>
        <div className="guide__text">
          <small>
            {formatDayLong(day.date)} · {places} {plural(places, 'место', 'места', 'мест')}
          </small>
          <h2>{day.title}</h2>
        </div>
      </section>

      <DayMap day={day} index={index} />

      <ol className="trail">
        {day.stops.map((stop, i) => (
          <li key={`${index}-${i}`} className="trail__item">
            <span className="trail__mark">{i + 1}</span>
            <div className="stop glass">
              <Photo className="photo stop__thumb" url={stop.photo} fallback={fallback} />
              <strong>{stop.name}</strong>
            </div>
          </li>
        ))}
      </ol>
    </Screen>
  );
}
