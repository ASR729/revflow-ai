import { formatBarWidth, formatRate } from '@/lib/format';

/**
 * PipelineBar — FE contract component.
 * `rate` is number | null straight from /metrics; null renders '—' (never 0%).
 * Bar width uses the same API value via a transform, not computed arithmetic.
 */
export function PipelineBar({
  label,
  rate,
  coverage,
  tone = 'navy',
}: {
  label: string;
  rate: number | null;
  coverage: string;
  tone?: 'navy' | 'recovered' | 'atrisk' | 'stopped' | 'simulated';
}) {
  const fill: Record<string, string> = {
    navy: 'bg-navy',
    recovered: 'bg-recovered',
    atrisk: 'bg-atrisk',
    stopped: 'bg-stopped',
    simulated: 'bg-simulated',
  };

  return (
    <div
      className="group"
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={rate === null ? undefined : rate}
      aria-valuetext={rate === null ? 'unavailable' : formatRate(rate)}
    >
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm font-medium text-ink">{label}</span>
        <span className="text-sm font-semibold tabular-nums text-ink">{formatRate(rate)}</span>
      </div>
      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-2 shadow-inner">
        {rate === null ? (
          <div className="h-full w-full bg-surface-2" />
        ) : (
          <div
            className={`h-full rounded-full ${fill[tone]} motion-safe:transition-[width] motion-safe:duration-500 motion-safe:ease-smooth`}
            style={{ width: formatBarWidth(rate) }}
          />
        )}
      </div>
      <p className="mt-1 text-xs text-muted">Coverage: {coverage}</p>
    </div>
  );
}
