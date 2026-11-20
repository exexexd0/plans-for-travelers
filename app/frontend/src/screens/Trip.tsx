import { useEffect, useRef, useState } from 'react';
import { DayMap } from '../DayMap';
import { formatRange, type Plan, type Trip as TripData } from '../state';
import { Actions, Button, Icon, RoundButton, Screen, Photo } from '../ui';

interface Props {
  plan: Plan;
  trip: TripData;
  onBack: () => void;
  onOpenPlace: (index: number) => void;
  onReset: () => void;
}

export function Trip({ plan, trip, onBack, onOpenPlace, onReset }: Props) {
  const [confirmReset, setConfirmReset] = useState(false);
  const day = trip.days[0];
  return (
    <Screen bg="water" veil={0.72} blur={40} flush>
      <Photo className="trip__photo" url={trip.cover} fallback={plan.interests[0]}>
        <RoundButton icon="chevron-left" label="Назад" onClick={onBack} />
      </Photo>

      <div className="trip__body">
        <div className="trip__head">
          <small className="accent">{formatRange(plan.start, plan.days)}</small>
          <h1>{trip.city}</h1>
        </div>
        <p>{trip.description.replace(/прогулка с детьми и природой/giu, 'Прогулка с детьми и время на природе')}</p>
        <DayMap day={day} />

        {day.stops.map((stop, i) => (
          <button key={`${stop.id}-${i}`} type="button" className="daycard glass" onClick={() => onOpenPlace(i)}>
            <Photo className="photo daycard__photo" url={stop.photo} fallback={plan.interests[0]}>
              <span className="tag">Место {i + 1}</span>
            </Photo>
            <span className="daycard__row">
              <strong>{stop.name}</strong>
              <span className="daycard__go" aria-hidden="true"><Icon name="arrow-right" /></span>
            </span>
            <small>{stop.address || 'Адрес не указан'}</small>
          </button>
        ))}
        <Button variant="secondary" onClick={() => setConfirmReset(true)}>Начать новый маршрут</Button>
      </div>
      {confirmReset && <ResetDialog onCancel={() => setConfirmReset(false)} onConfirm={onReset} />}
    </Screen>
  );
}

function ResetDialog({ onCancel, onConfirm }: { onCancel: () => void; onConfirm: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    element.showModal();
    return () => element.close();
  }, []);

  return (
    <dialog ref={dialog} className="reset-dialog" aria-labelledby="reset-title" aria-describedby="reset-description"
      onCancel={(event) => { event.preventDefault(); onCancel(); }}>
      <h2 id="reset-title">Вы уверены, что хотите начать сначала?</h2>
      <p id="reset-description">Ваш прогресс заполнения будет утерян.</p>
      <Actions>
        <Button variant="secondary" onClick={onCancel} autoFocus>Отмена</Button>
        <Button onClick={onConfirm}>Начать сначала</Button>
      </Actions>
    </dialog>
  );
}