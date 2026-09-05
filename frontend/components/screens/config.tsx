'use client';

import { api, type ConfigResponse } from '@/lib/api';
import { useApiData } from '@/lib/use-api-data';
import { PageHeader } from '@/components/app-shell';
import { ErrorState, PageSkeleton } from '@/components/ui/states';
import { Tag } from '@/components/ui/badge';
import { formatCount } from '@/lib/format';

const DESCRIPTIONS: Record<string, string> = {
  MAX_RETRIES: 'Hard ceiling on automatic retries per event.',
  COOLDOWN_HOURS: 'Minimum quiet hours between contacts for one customer.',
  RETRY_BACKOFF_HOURS: 'Retry schedule spacing, in hours.',
  CHECKOUT_SESSION_WINDOW_MINUTES: 'How long an abandoned checkout stays resumable.',
  MAX_CONTACTS_PER_CUSTOMER_PER_DAY: 'Contact cap guarding against harassment.',
  STOP_IF_CAUSE_IN: 'Causes that force an immediate stop.',
  LADDER_GENTLE_AFTER_DAYS: 'Days overdue before the gentle reminder step.',
  LADDER_FIRM_AFTER_DAYS: 'Days overdue before the firm reminder step.',
  LADDER_FLAG_AFTER_DAYS: 'Days overdue before flagging for a human.',
  PTP_GRACE_DAYS: 'Grace days after a promise-to-pay date.',
  LLM_CALL_BUDGET_PER_RUN: 'Maximum LLM calls allowed per batch run.',
  LLM_MAX_ATTEMPTS: 'LLM request attempts before the deterministic fallback.',
  LLM_TIMEOUT_SECONDS: 'Per-call LLM timeout.',
  BATCH_SIZE: 'Events per batch run.',
  RANDOM_SEED: 'Deterministic run seed.',
  DECISION_LATENCY_BUDGET_MS: 'Per-decision latency budget.',
};

export function ConfigScreen() {
  const state = useApiData<ConfigResponse>(() => api.getConfig());

  return (
    <div>
      <PageHeader
        title="Configuration"
        description="The policy ceiling the agent operates under. Read-only — set at deploy time."
      />

      {state.status === 'loading' ? (
        <PageSkeleton rows={3} />
      ) : state.status === 'error' ? (
        <ErrorState title="Unable to load configuration." message={state.message} />
      ) : (
        <ConfigBody config={state.data} />
      )}
    </div>
  );
}

function ConfigBody({ config }: { config: ConfigResponse }) {
  const entries = Object.entries(config).filter(([key]) => key !== 'editable' && key !== 'note');
  return (
    <div className="card p-5">
      <div className="mb-4 flex items-center gap-2">
        <Tag label={config.editable ? 'Editable' : 'Read-only'} tone={config.editable ? 'atrisk' : 'neutral'} />
        <p className="text-xs text-muted">{config.note}</p>
      </div>
      <dl className="divide-y divide-edge">
        {entries.map(([key, value]) => (
          <div key={key} className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-[240px_1fr_200px] sm:gap-4">
            <dt className="font-mono text-xs font-semibold text-ink">{key}</dt>
            <dd className="text-sm text-muted">{DESCRIPTIONS[key] ?? 'Policy parameter.'}</dd>
            <dd className="text-sm font-medium tabular-nums text-ink sm:text-right">
              {Array.isArray(value)
                ? value
                    .map((v) => (typeof v === 'number' ? formatCount(v) : String(v)))
                    .join(', ')
                : typeof value === 'number'
                  ? formatCount(value)
                  : String(value)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
