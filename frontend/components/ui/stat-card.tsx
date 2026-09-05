import type { ReactNode } from 'react';

/**
 * StatCard — FE contract component.
 * Accepts number | null; null renders '—', never 0.
 * `format` converts number -> display string via lib/format only.
 */
export function StatCard({
  label,
  value,
  format,
  caption,
  tone = 'navy',
  ariaLabel,
}: {
  label: string;
  value: number | null;
  format: (n: number) => string;
  caption?: string;
  tone?: 'navy' | 'recovered' | 'atrisk' | 'stopped' | 'simulated';
  ariaLabel?: string;
}) {
  const accent: Record<string, string> = {
    navy: 'bg-navy',
    recovered: 'bg-recovered',
    atrisk: 'bg-atrisk',
    stopped: 'bg-stopped',
    simulated: 'bg-simulated',
  };

  return (
    <div
      className="card-3d relative overflow-hidden p-5"
      role="group"
      aria-label={ariaLabel ?? `${label}: ${value === null ? 'unavailable' : format(value)}`}
    >
      <span aria-hidden="true" className={`absolute inset-x-0 top-0 h-0.5 ${accent[tone]}`} />
      <p className="eyebrow">{label}</p>
      <p className="stat-value mt-2">{value === null ? '—' : format(value)}</p>
      {caption ? <p className="mt-1 text-xs text-muted">{caption}</p> : null}
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="card p-5" aria-hidden="true">
      <div className="skeleton h-3 w-24" />
      <div className="skeleton mt-3 h-7 w-32" />
      <div className="skeleton mt-2 h-3 w-20" />
    </div>
  );
}

export function CardSection({
  title,
  subtitle,
  children,
  actions,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section className="card-3d p-5 sm:p-6">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-sm text-muted">{subtitle}</p> : null}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
