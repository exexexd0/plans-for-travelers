import { useState } from 'react';
import { addDays, fromISO, toISO, todayISO } from './state';
import { Icon } from './ui';

const MONTHS = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
];
const WEEK = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];

interface Props {
  /** yyyy-mm-dd, первый день поездки */
  start: string;
  days: number;
  onPick: (iso: string) => void;
}

export function Calendar({ start, days, onPick }: Props) {
  const today = todayISO();
  const end = toISO(addDays(start, days - 1));
  const [view, setView] = useState(() => {
    const d = fromISO(start);
    return { y: d.getFullYear(), m: d.getMonth() };
  });

  const shift = (n: number) => {
    const d = new Date(view.y, view.m + n, 1);
    setView({ y: d.getFullYear(), m: d.getMonth() });
  };

  const now = fromISO(today);
  const atCurrentMonth = view.y === now.getFullYear() && view.m === now.getMonth();
  // неделя начинается с понедельника
  const offset = (new Date(view.y, view.m, 1).getDay() + 6) % 7;
  const count = new Date(view.y, view.m + 1, 0).getDate();

  return (
    <div className="cal">
      <div className="cal__head">
        <h2>
          {MONTHS[view.m]} <span>{view.y}</span>
        </h2>
        <button type="button" className="cal__nav" aria-label="Предыдущий месяц" disabled={atCurrentMonth} onClick={() => shift(-1)}>
          <Icon name="chevron-left" size={18} />
        </button>
        <button type="button" className="cal__nav cal__nav--next" aria-label="Следующий месяц" onClick={() => shift(1)}>
          <Icon name="chevron-left" size={18} />
        </button>
      </div>

      <div className="cal__grid cal__week" aria-hidden="true">
        {WEEK.map((w) => (
          <span key={w}>{w}</span>
        ))}
      </div>

      <div className="cal__grid">
        {Array.from({ length: offset }, (_, i) => (
          <span key={`e${i}`} />
        ))}
        {Array.from({ length: count }, (_, i) => {
          const iso = toISO(new Date(view.y, view.m, i + 1));
          const cls = ['cal__day'];
          if (iso >= start && iso <= end) cls.push('cal__day--in');
          if (iso === start) cls.push('cal__day--start');
          if (iso === end) cls.push('cal__day--end');
          if (iso === today) cls.push('cal__day--today');
          return (
            <button
              key={iso}
              type="button"
              className={cls.join(' ')}
              disabled={iso < today}
              aria-pressed={iso === start}
              aria-label={`${i + 1}, ${MONTHS[view.m].toLowerCase()}`}
              onClick={() => onPick(iso)}
            >
              <span>{i + 1}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
