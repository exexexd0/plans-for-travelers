import { Calendar } from '../Calendar';
import { DURATIONS, addDays, durationLabel, formatDay, fromISO, type Plan } from '../state';
import { Actions, Button, Chip, Heading, Screen, TopBar } from '../ui';

interface Props {
  plan: Plan;
  onChange: (p: Partial<Plan>) => void;
  onCancel: () => void;
  onBack: () => void;
  onNext: () => void;
}

export function Duration({ plan, onChange, onCancel, onBack, onNext }: Props) {
  // 0 = длительность не выбрана: даты показываем как для одного дня, «Далее» недоступна
  const days = plan.days || 1;

  return (
    <Screen bg="water">
      <TopBar step={3} onCancel={onCancel} />
      <Heading title="Сколько времени у тебя есть?" sub="Рассчитаем маршрут так, чтобы всё успеть" />

      <div className="chips">
        {DURATIONS.map((d) => (
          <Chip key={d} active={d === plan.days} onClick={() => onChange({ days: d === plan.days ? 0 : d })}>
            {durationLabel(d)}
          </Chip>
        ))}
      </div>

      <div className="dates glass">
        <Calendar start={plan.start} days={days} onPick={(iso) => onChange({ start: iso })} />
        <div className="dates__journal">
          <div>
            <small>Начало</small>
            <strong>{formatDay(fromISO(plan.start))}</strong>
          </div>
          <svg width="88" height="20" viewBox="0 0 88 20" fill="none" aria-hidden="true">
            <path d="M8 10 C 24 0, 40 20, 56 10 S 74 4, 80 10" stroke="#4E9A6B" strokeWidth="2" strokeLinecap="round" strokeDasharray="0.5 6" />
            <circle cx="8" cy="10" r="4" fill="#4E9A6B" />
            <circle cx="80" cy="10" r="4" fill="#fff" stroke="#357A52" strokeWidth="2" />
          </svg>
          <div className="dates__end">
            <small>Конец</small>
            <strong>{formatDay(addDays(plan.start, days - 1))}</strong>
          </div>
        </div>
      </div>

      <div className="grow" />
      <Actions>
        <Button variant="secondary" className="btn--back" onClick={onBack}>
          Назад
        </Button>
        <Button disabled={plan.days === 0} onClick={onNext}>
          Далее
        </Button>
      </Actions>
    </Screen>
  );
}
