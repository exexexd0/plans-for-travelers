import { useEffect, useMemo, useState } from 'react';
import { buildRoute, todayISO, type Plan, type Step } from './state';
import { City } from './screens/City';
import { Interests } from './screens/Interests';
import { Duration } from './screens/Duration';
import { Review } from './screens/Review';
import { Generating } from './screens/Generating';
import { Trip } from './screens/Trip';
import { Route } from './screens/Route';

const emptyPlan = (): Plan => ({ city: '', interests: [], days: 2, start: todayISO() });

export function App() {
  const [step, setStep] = useState<Step>('city');
  const [plan, setPlan] = useState<Plan>(emptyPlan);
  const [day, setDay] = useState(0);
  const route = useMemo(() => buildRoute(plan), [plan]);

  // рамка телефона 390×844 уменьшается целиком, если окно ниже неё
  useEffect(() => {
    const fit = () => {
      const scale = Math.min(1, (window.innerHeight - 32) / 844, window.innerWidth / 390);
      document.documentElement.style.setProperty('--phone-scale', String(scale));
    };
    fit();
    window.addEventListener('resize', fit);
    return () => window.removeEventListener('resize', fit);
  }, []);

  const patch = (p: Partial<Plan>) => setPlan((prev) => ({ ...prev, ...p }));
  const reset = () => {
    setPlan(emptyPlan());
    setStep('city');
  };

  let screen;
  switch (step) {
    case 'city':
      screen = <City plan={plan} onChange={patch} onCancel={reset} onNext={() => setStep('interests')} />;
      break;
    case 'interests':
      screen = <Interests plan={plan} onChange={patch} onCancel={reset} onBack={() => setStep('city')} onNext={() => setStep('duration')} />;
      break;
    case 'duration':
      screen = <Duration plan={plan} onChange={patch} onCancel={reset} onBack={() => setStep('interests')} onNext={() => setStep('review')} />;
      break;
    case 'review':
      screen = <Review plan={plan} onCancel={reset} onEdit={setStep} onBack={() => setStep('duration')} onNext={() => setStep('generating')} />;
      break;
    case 'generating':
      screen = <Generating onDone={() => setStep('trip')} />;
      break;
    case 'trip':
      screen = (
        <Trip
          plan={plan}
          route={route}
          onBack={() => setStep('review')}
          onOpenDay={(i) => {
            setDay(i);
            setStep('route');
          }}
        />
      );
      break;
    case 'route':
      screen = <Route route={route} initial={day} onBack={() => setStep('trip')} />;
      break;
  }

  return (
    <div className="phone">
      <div className="phone__view" key={step}>
        {screen}
      </div>
    </div>
  );
}
