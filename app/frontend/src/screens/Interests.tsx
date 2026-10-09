import { INTERESTS, type Plan } from '../state';
import { Actions, Button, Heading, Icon, Screen, TopBar } from '../ui';

interface Props {
  plan: Plan;
  onChange: (p: Partial<Plan>) => void;
  onCancel: () => void;
  onBack: () => void;
  onNext: () => void;
}

export function Interests({ plan, onChange, onCancel, onBack, onNext }: Props) {
  const selected = plan.interests;
  const toggle = (id: string) =>
    onChange({ interests: selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id] });

  return (
    <Screen bg="water">
      <TopBar step={2} onCancel={onCancel} />
      <Heading title="Что важно в маршруте?" sub="Выбери, что хочешь увидеть — можно несколько вариантов" />

      <div className="interests">
        {INTERESTS.map((it) => {
          const active = selected.includes(it.id);
          return (
            <button
              key={it.id}
              type="button"
              className={`interest glass${active ? ' interest--active' : ''}`}
              aria-pressed={active}
              onClick={() => toggle(it.id)}
            >
              <span className="interest__top">
                <Icon name={it.icon} />
              </span>
              <span className="interest__label">{it.label}</span>
            </button>
          );
        })}
      </div>

      <div className="grow" />
      <Actions>
        <Button variant="secondary" className="btn--back" onClick={onBack}>
          Назад
        </Button>
        <Button disabled={selected.length === 0} onClick={onNext}>
          Далее
        </Button>
      </Actions>
    </Screen>
  );
}
