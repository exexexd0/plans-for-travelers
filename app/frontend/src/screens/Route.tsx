import { DayMap } from '../DayMap';
import { type RouteDay } from '../state';
import { RoundButton, Screen, Photo } from '../ui';

export function Route({ day, placeIndex, fallback, onBack }: {
  day: RouteDay; placeIndex: number; fallback: string; onBack: () => void;
}) {
  const stop = day.stops[placeIndex];

  return (
    <Screen bg="water" veil={0.7} blur={34}>
      <header className="route__top">
        <RoundButton icon="chevron-left" label="Назад" onClick={onBack} />
        <h1>Место {placeIndex + 1}</h1>
      </header>

      <section className="guide glass">
        <Photo className="photo guide__photo" url={stop.photo} fallback={fallback}>
          <span className="tag">Место {placeIndex + 1}</span>
        </Photo>
        <div className="guide__text">
          <h2>{stop.name}</h2>
          <p>{stop.description || 'Описание отсутствует'}</p>
          <small>{stop.address || 'Адрес не указан'}</small>
        </div>
      </section>

      <DayMap day={day} placeIndex={placeIndex} />
    </Screen>
  );
}
