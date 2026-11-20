import { Calendar } from '../Calendar';
import type { Plan } from '../state';
import { Actions, Button, Heading, Screen, TopBar } from '../ui';

interface Props {
  plan: Plan;
  onChange: (p: Partial<Plan>) => void;
  onCancel: () => void;
  onBack: () => void;
  onNext: () => void;
}

export function Duration({ plan, onChange, onCancel, onBack, onNext }: Props) {
  const days = 1;

  return (
    <Screen bg="water">
      <TopBar step={3} onCancel={onCancel} />
      <Heading title="Когда отправимся?" sub="Выбери дату маршрута" />

      <div className="dates glass">
        <Calendar start={plan.start} days={days} onPick={(iso) => onChange({ start: iso })} />
      </div>

      <div className="grow" />
      <Actions>
        <Button variant="secondary" className="btn--back" onClick={onBack}>
          Назад
        </Button>
        <Button onClick={onNext}>
          Далее
        </Button>
      </Actions>
    </Screen>
  );
}
