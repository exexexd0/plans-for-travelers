import { formatDayLong, formatRange, type Plan, type Trip as TripData } from '../state';
import { Icon, RoundButton, Screen, Photo } from '../ui';

interface Props {
  plan: Plan;
  trip: TripData;
  onBack: () => void;
  onOpenDay: (index: number) => void;
}

export function Trip({ plan, trip, onBack, onOpenDay }: Props) {
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
        <p>{trip.description}</p>

        {trip.days.map((day, i) => (
          <button key={i} type="button" className="daycard glass" onClick={() => onOpenDay(i)}>
            <Photo className="photo daycard__photo" url={day.cover} fallback={plan.interests[0]}>
              <span className="tag">День {i + 1}</span>
            </Photo>
            <span className="daycard__row">
              <Icon name="calendar" />
              <strong>{formatDayLong(day.date)}</strong>
              <span className="daycard__go" aria-hidden="true">
                <Icon name="arrow-right" />
              </span>
            </span>
            <small>{day.summary}</small>
          </button>
        ))}
      </div>
    </Screen>
  );
}
