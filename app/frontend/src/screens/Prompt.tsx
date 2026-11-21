import { useState } from 'react';
import { Actions, Button, Heading, Progress, Screen } from '../ui';

interface Props {
  initialPrompt: string | null | undefined;
  onCancel: () => void;
  onBack: () => void;
  onNext: (prompt: string | null) => void;
}

export function Prompt({ initialPrompt, onCancel, onBack, onNext }: Props) {
  const [draft, setDraft] = useState(initialPrompt ?? '');

  return (
    <Screen bg="water">
      <header className="topbar">
        <Progress step={2} />
        <button type="button" className="chip" onClick={onCancel}>Отменить</button>
      </header>
      <Heading title="Что-то ещё?" sub="Вы можете добавить более подробные пожелания к маршруту." />

      <label className="prompt__field glass">
        <textarea
          aria-label="Пожелания к маршруту"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Например: Я хочу сходить в парк, после чего поесть и зайти в торговый центр."
          rows={6}
        />
      </label>

      <div className="grow" />
      <Actions>
        <Button variant="secondary" className="btn--back" onClick={onBack}>Назад</Button>
        <Button onClick={() => onNext(draft.trim() || null)}>Далее</Button>
      </Actions>
    </Screen>
  );
}
