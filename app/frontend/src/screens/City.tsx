import { CITIES, type Plan } from '../state';
import { Actions, Button, Chip, Heading, Icon, Screen, TopBar, img } from '../ui';

interface Props {
  plan: Plan;
  onChange: (p: Partial<Plan>) => void;
  onCancel: () => void;
  onNext: () => void;
}

const TRAIL = 'M66 214 C 110 190, 120 150, 170 150 S 250 170, 262 116 S 220 70, 250 46';

export function City({ plan, onChange, onCancel, onNext }: Props) {
  const city = plan.city;
  const ready = city.trim().length > 0;

  return (
    <Screen bg="water">
      <TopBar step={1} onCancel={onCancel} />
      <Heading title="Откуда начнём?" sub="Выбери город или регион — дальше подберём интересы и соберём персональный маршрут" />

      <div className="hero" aria-hidden="true">
        <div className="hero__art">
          <div className="pebble pebble--a" style={{ backgroundImage: `url(${img('glasswave')})` }} />
          <div className="pebble pebble--b" style={{ backgroundImage: `url(${img('lily')})` }} />
          <div className="pebble pebble--c" style={{ backgroundImage: `url(${img('pinkgrass')})` }} />
          <svg className="hero__trail" viewBox="0 0 342 280" fill="none">
            <path d={TRAIL} stroke="#fff" strokeOpacity="0.85" strokeWidth="6" strokeLinecap="round" />
            <path d={TRAIL} stroke="#235C3B" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="0.5 7" />
            <path d="M66 214 C 110 190, 120 150, 170 150" stroke="#235C3B" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="66" cy="214" r="6" fill="#235C3B" stroke="#fff" strokeWidth="2" />
            <circle cx="170" cy="150" r="6" fill="#fff" stroke="#235C3B" strokeWidth="2.5" />
            <circle cx="262" cy="116" r="4.5" fill="#fff" stroke="#235C3B" strokeWidth="1.5" />
            <circle cx="250" cy="46" r="22" fill="#fff" fillOpacity="0.35" />
            <circle cx="250" cy="46" r="13" fill="#fff" fillOpacity="0.55" />
            <circle cx="250" cy="46" r="7" fill="#fff" stroke="#235C3B" strokeWidth="2.5" />
          </svg>
        </div>
      </div>

      <form
        className="stack"
        onSubmit={(e) => {
          e.preventDefault();
          if (ready) onNext();
        }}
      >
        <label className={`search glass${ready ? ' search--filled' : ''}`}>
          <Icon name="search" />
          <input
            type="text"
            value={city}
            placeholder="Город или регион"
            aria-label="Город или регион"
            autoComplete="off"
            enterKeyHint="next"
            onChange={(e) => onChange({ city: e.target.value })}
          />
          {ready && (
            <button type="button" className="search__clear" aria-label="Очистить" onClick={() => onChange({ city: '' })}>
              <Icon name="x" size={14} strokeWidth={2.6} />
            </button>
          )}
        </label>
        <div className="chips">
          {CITIES.map((c) => (
            <Chip key={c} active={c === city} onClick={() => onChange({ city: c === city ? '' : c })}>
              {c}
            </Chip>
          ))}
        </div>
      </form>

      <Actions>
        <Button variant="secondary" className="btn--back" onClick={onCancel}>
          Назад
        </Button>
        <Button disabled={!ready} onClick={onNext}>
          Далее
        </Button>
      </Actions>
    </Screen>
  );
}
