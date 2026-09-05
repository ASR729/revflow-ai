import type { Tone } from '@/lib/labels';

const TONE_CLASS: Record<Tone, string> = {
  recovered: 'bg-recovered/10 text-recovered',
  atrisk: 'bg-atrisk/10 text-atrisk',
  stopped: 'bg-stopped/10 text-stopped',
  simulated: 'bg-simulated/10 text-simulated',
  navy: 'bg-navy/10 text-navy',
  neutral: 'bg-surface-2 text-muted',
};

export function Tag({ label, tone }: { label: string; tone: Tone }) {
  return <span className={`badge ${TONE_CLASS[tone]}`}>{label}</span>;
}

export function Dot({ tone }: { tone: Tone }) {
  const fill: Record<Tone, string> = {
    recovered: 'bg-recovered',
    atrisk: 'bg-atrisk',
    stopped: 'bg-stopped',
    simulated: 'bg-simulated',
    navy: 'bg-navy',
    neutral: 'bg-muted',
  };
  return <span aria-hidden="true" className={`inline-block h-2 w-2 rounded-full ${fill[tone]}`} />;
}
