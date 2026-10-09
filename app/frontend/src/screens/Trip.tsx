import { formatDayLong, formatRange, tripDescription, type Plan, type RouteDay } from '../state';
import { Icon, RoundButton, Screen, img } from '../ui';

interface Props {
  plan: Plan;
  route: RouteDay[];
  onBack: () => void;
  onOpenDay: (index: number) => void;
}

export function Trip({ plan, route, onBack, onOpenDay }: Props) {
  return (
    <Screen bg="water" veil={0.72} blur={40} flush>
      <div className="trip__photo" style={{ backgroundImage: `url(${img('forestpath')})` }}>
        <RoundButton icon="chevron-left" label="Назад" onClick={onBack} />
      </div>

      <div className="trip__body">
        <div className="trip__head">
          <small className="accent">{formatRange(plan.start, plan.days)}</small>
          <h1>{plan.city}</h1>
        </div>
        <p>{tripDescription(plan)}</p>

        {route.map((day, i) => (
          <button key={i} type="button" className="daycard glass" onClick={() => onOpenDay(i)}>
            <span className="photo daycard__photo" style={{ backgroundImage: `url(${img(day.cover)})` }}>
              <span className="tag">День {i + 1}</span>
            </span>
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
