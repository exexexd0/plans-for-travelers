import type { ButtonHTMLAttributes, ReactNode } from 'react';

// ---------- icons ----------

const ICONS = {
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  x: <path d="M18 6 6 18M6 6l12 12" />,
  check: <path d="M20 6 9 17l-5-5" />,
  'chevron-left': <path d="m15 18-6-6 6-6" />,
  'arrow-right': <path d="M5 12h14M13 6l6 6-6 6" />,
  calendar: <><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></>,
  pencil: <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />,
  compass: <><circle cx="12" cy="12" r="10" /><path d="m16.2 7.8-2.1 6.3-6.3 2.1 2.1-6.3z" /></>,
  kids: <><circle cx="12" cy="12" r="10" /><path d="M8 14s1.5 2 4 2 4-2 4-2M9 9v.5M15 9v.5" /></>,
  coffee: <path d="M17 8h1a4 4 0 1 1 0 8h-1M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4ZM6 2v3M10 2v3M14 2v3" />,
  tree: <path d="M12 22v-7M12 16c-3.5 0-6-2.6-6-6.2a6 6 0 0 1 12 0c0 3.6-2.5 6.2-6 6.2ZM12 13l2.5-2.5M12 10.5 10 8.5" />,
  landmark: <path d="M3 21h18M6 17v-6M10 17v-6M14 17v-6M18 17v-6M12 3l8 5H4z" />,
  image: <><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="9" cy="9" r="2" /><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21" /></>,
  mountain: <path d="m8 3 4 8 5-5 5 15H2L8 3z" />,
  sparkles: <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9zM19 16v4M17 18h4M5 3v3M3.5 4.5h3" />,
  moon: <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />,
} satisfies Record<string, ReactNode>;

export type IconName = keyof typeof ICONS;

export function Icon({ name, size = 24, strokeWidth = 1.7 }: { name: IconName; size?: number; strokeWidth?: number }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {ICONS[name]}
    </svg>
  );
}

export const img = (name: string) => `${import.meta.env.BASE_URL}img/${name}.jpg`;

// ---------- screen shell ----------

interface ScreenProps {
  bg: string;
  /** opacity of the light veil over the photo, 0 = none */
  veil?: number;
  blur?: number;
  topo?: boolean;
  /** no side/top padding: content manages its own (photo header) */
  flush?: boolean;
  children: ReactNode;
}

export function Screen({ bg, veil = 0.58, blur = 26, topo = true, flush = false, children }: ScreenProps) {
  return (
    <section className={`screen${flush ? ' screen--flush' : ''}`}>
      <div
        className="screen__bg"
        style={{ backgroundImage: `url(${img(bg)})`, filter: blur ? `blur(${blur}px)` : undefined, inset: blur ? -50 : 0 }}
      />
      {veil > 0 && <div className="screen__veil" style={{ opacity: veil }} />}
      {topo && (
        <svg className="screen__topo" viewBox="0 0 390 844" preserveAspectRatio="none" aria-hidden="true">
          {[0, 1, 2, 3, 4, 5].map((i) => {
            const y = 540 + i * 24;
            return <path key={i} d={`M-20 ${y} C 80 ${y - 46 + i * 4}, 190 ${y + 52 - i * 5}, 410 ${y - 14}`} />;
          })}
        </svg>
      )}
      <div className="screen__content">{children}</div>
    </section>
  );
}

// ---------- progress ----------

export function Progress({ step }: { step: 1 | 2 | 3 }) {
  const a = 'M10 12 C 28 3, 46 21, 64 12';
  const b = ' S 100 3, 118 12';
  const points = [10, 64, 118];
  return (
    <svg className="progress" width="128" height="24" viewBox="0 0 128 24" fill="none" role="img" aria-label={`Шаг ${step} из 3`}>
      <path d={a + b} stroke="#1F2E27" strokeOpacity="0.16" strokeWidth="2" strokeLinecap="round" />
      {step > 1 && <path d={step > 2 ? a + b : a} stroke="#4E9A6B" strokeWidth="2.5" strokeLinecap="round" />}
      {points.map((x, i) => {
        if (i < step - 1) return <circle key={x} cx={x} cy="12" r="5" fill="#4E9A6B" />;
        if (i === step - 1) {
          return (
            <g key={x}>
              <circle cx={x} cy="12" r="10" fill="#4E9A6B" fillOpacity="0.2" />
              <circle cx={x} cy="12" r="5.5" fill="#fff" stroke="#357A52" strokeWidth="2.5" />
            </g>
          );
        }
        return <circle key={x} cx={x} cy="12" r="4" fill="#fff" stroke="#1F2E27" strokeOpacity="0.28" strokeWidth="1.5" />;
      })}
    </svg>
  );
}

export function TopBar({ step, onCancel }: { step: 1 | 2 | 3; onCancel: () => void }) {
  return (
    <header className="topbar">
      <button type="button" className="chip" onClick={onCancel}>
        Отменить
      </button>
      <Progress step={step} />
    </header>
  );
}

export function Heading({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="heading">
      <h1>{title}</h1>
      {sub && <p>{sub}</p>}
    </div>
  );
}

// ---------- controls ----------

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
}

export function Button({ variant = 'primary', className = '', type = 'button', ...rest }: ButtonProps) {
  return <button type={type} className={`btn btn--${variant} ${className}`} {...rest} />;
}

interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

export function Chip({ active = false, children, className = '', ...rest }: ChipProps) {
  return (
    <button type="button" className={`chip${active ? ' chip--active' : ''} ${className}`} aria-pressed={active} {...rest}>
      {children}
    </button>
  );
}

export function RoundButton({ icon, label, size = 44, ...rest }: { icon: IconName; label: string; size?: number } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button type="button" className="round" style={{ width: size, height: size }} aria-label={label} {...rest}>
      <Icon name={icon} />
    </button>
  );
}

export function Actions({ children }: { children: ReactNode }) {
  return <div className="actions">{children}</div>;
}
