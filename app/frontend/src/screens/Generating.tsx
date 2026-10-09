import { useEffect, useState } from 'react';
import { Button, Screen } from '../ui';

const FULL = 'M50 520 C 130 500, 70 420, 150 400 S 290 420, 300 330 S 170 270, 196 200 S 290 160, 330 116';
const DONE = 'M50 520 C 130 500, 70 420, 150 400 S 290 420, 300 330';
const GENERATION_MS = 4200;

export function Generating({ onDone }: { onDone: () => void }) {
  const [note, setNote] = useState('');

  useEffect(() => {
    const t = window.setTimeout(onDone, GENERATION_MS);
    return () => window.clearTimeout(t);
  }, [onDone]);

  const share = async () => {
    const data = { title: 'VK Места', text: 'Собираю маршрут в VK Места — присоединяйся', url: window.location.href };
    try {
      if (navigator.share) {
        await navigator.share(data);
      } else {
        await navigator.clipboard.writeText(data.url);
        setNote('Ссылка скопирована');
      }
    } catch {
      // пользователь закрыл окно «Поделиться» или буфер недоступен — ничего не делаем
    }
  };

  return (
    <Screen bg="motion" veil={0} blur={0} topo={false}>
      <svg className="gen" viewBox="0 0 390 600" fill="none" preserveAspectRatio="xMidYMin slice" aria-hidden="true">
        <path d={FULL} stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="0.5 8" />
        <path className="gen__glow" d={DONE} pathLength={1} stroke="#fff" strokeOpacity="0.35" strokeWidth="12" strokeLinecap="round" />
        <path className="gen__line" d={DONE} pathLength={1} stroke="#fff" strokeWidth="3.5" strokeLinecap="round" />
        <g className="gen__point" style={{ animationDelay: '0.1s' }}>
          <circle cx="50" cy="520" r="15" fill="#fff" fillOpacity="0.35" />
          <circle cx="50" cy="520" r="7" fill="#fff" stroke="#235C3B" strokeWidth="2.5" />
        </g>
        <g className="gen__point" style={{ animationDelay: '1.2s' }}>
          <circle cx="150" cy="400" r="15" fill="#fff" fillOpacity="0.35" />
          <circle cx="150" cy="400" r="7" fill="#fff" stroke="#235C3B" strokeWidth="2.5" />
        </g>
        <g className="gen__point" style={{ animationDelay: '2.6s' }}>
          <circle cx="300" cy="330" r="32" fill="#fff" fillOpacity="0.22" />
          <circle cx="300" cy="330" r="19" fill="#fff" fillOpacity="0.42" />
          <circle cx="300" cy="330" r="8" fill="#fff" stroke="#235C3B" strokeWidth="3" />
        </g>
        <circle cx="196" cy="200" r="5" fill="#fff" fillOpacity="0.9" />
        <circle cx="330" cy="116" r="5" fill="#fff" fillOpacity="0.9" />
      </svg>

      <div className="grow" />
      <div className="message glass" role="status" aria-live="polite">
        <h1>Секундочку...</h1>
        <p>Маршрут почти готов. Это отличный повод рассказать о нас друзьям, чтобы открывать новые места вместе</p>
        <Button onClick={share}>{note || 'Рекомендовать VK Места'}</Button>
      </div>
    </Screen>
  );
}
