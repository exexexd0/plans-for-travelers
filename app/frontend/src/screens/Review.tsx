import type { ReactNode } from 'react';
import { INTERESTS, formatRange, type Plan, type Step } from '../state';
import { Actions, Button, Icon, Screen, TopBar, img } from '../ui';

interface Props {
  plan: Plan;
  onCancel: () => void;
  onEdit: (step: Step) => void;
  onBack: () => void;
  onNext: () => void;
}

function Card({ label, onEdit, children }: { label: string; onEdit: () => void; children: ReactNode }) {
  return (
    <section className="review glass">
      <div className="review__top">
        <small>{label}</small>
        <button type="button" className="edit" onClick={onEdit}>
          <Icon name="pencil" size={16} />
          Изменить
        </button>
      </div>
      {children}
    </section>
  );
}

export function Review({ plan, onCancel, onEdit, onBack, onNext }: Props) {
  const chosen = INTERESTS.filter((i) => plan.interests.includes(i.id));

  return (
    <Screen bg="water">
      <TopBar step={3} onCancel={onCancel} />
      <div className="heading">
        <h1>Проверь, всё ли верно</h1>
      </div>

      <div className="stack">
        <Card label="Город или регион" onEdit={() => onEdit('city')}>
          <div className="review__city">
            <span className="photo review__thumb" style={{ backgroundImage: `url(${img('forestpath')})` }} />
            <h2>{plan.city}</h2>
          </div>
        </Card>
        <Card label="Маршрут включает" onEdit={() => onEdit('interests')}>
          <ul className="checklist">
            {chosen.map((i) => (
              <li key={i.id}>
                <Icon name="check" size={16} strokeWidth={2.6} />
                {i.label}
              </li>
            ))}
          </ul>
        </Card>
        <Card label="Даты" onEdit={() => onEdit('duration')}>
          <h2>{formatRange(plan.start, plan.days)}</h2>
        </Card>
      </div>

      <div className="grow" />
      <Actions>
        <Button variant="secondary" className="btn--back" onClick={onBack}>
          Назад
        </Button>
        <Button onClick={onNext}>Всё верно, вперёд</Button>
      </Actions>
    </Screen>
  );
}
