'use client';

import { useEffect, useState } from 'react';
import { api, type EventDetailResponse } from '@/lib/api';
import { PageHeader } from '@/components/app-shell';
import { ErrorState, PageSkeleton } from '@/components/ui/states';
import { Tag } from '@/components/ui/badge';
import {
  ACTION_LABEL,
  ACTION_TONE,
  EVENT_TYPE_LABEL,
  LADDER_LABEL,
  LADDER_TONE,
  OUTCOME_LABEL,
  OUTCOME_TONE,
  RULE_LABEL,
  labelFor,
} from '@/lib/labels';
import { formatCount, formatINRLedger, formatLatency, formatTimestamp } from '@/lib/format';

export function EventDetailScreen({ eventId }: { eventId: string }) {
  const [state, setState] = useState<
    { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: EventDetailResponse }
  >({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    api
      .getEventDetail(eventId)
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: 'error',
            message: err instanceof Error ? err.message : 'Unable to load this event.',
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [eventId]);

  return (
    <div>
      <PageHeader title="Event detail" description={`Decision lineage for ${eventId}.`} />
      {state.status === 'loading' ? (
        <PageSkeleton rows={3} />
      ) : state.status === 'error' ? (
        <ErrorState title="Event unavailable." message={state.message} />
      ) : (
        <Detail detail={state.data} />
      )}
    </div>
  );
}

function Detail({ detail }: { detail: EventDetailResponse }) {
  const ev = detail.event;
  return (
    <div className="space-y-4">
      <section className="card p-5" aria-label="Event summary">
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-xs text-muted">Pipeline</dt>
            <dd className="text-sm font-medium text-ink">{labelFor(EVENT_TYPE_LABEL, ev.event_type)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Amount</dt>
            <dd className="font-mono text-sm font-medium text-ink">{formatINRLedger(ev.amount_inr)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Customer</dt>
            <dd className="font-mono text-sm text-ink">{ev.customer_id}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Ladder step</dt>
            <dd>
              <Tag label={labelFor(LADDER_LABEL, ev.ladder_step)} tone={LADDER_TONE[ev.ladder_step] ?? 'neutral'} />
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Decline code</dt>
            <dd className="text-sm text-ink">{ev.decline_code ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Recorded</dt>
            <dd className="text-sm text-ink">{formatTimestamp(ev.created_at)}</dd>
          </div>
        </dl>
      </section>

      <section className="card p-5" aria-label="Decision timeline">
        <h2 className="eyebrow mb-3">Decision timeline</h2>
        {detail.timeline.length === 0 ? (
          <p className="text-sm text-muted">No audit entries for this event.</p>
        ) : (
          <ol className="space-y-3">
            {detail.timeline.map((row) => (
              <li key={row.id} className="rounded-card border border-edge bg-canvas p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Tag label={labelFor(ACTION_LABEL, row.action)} tone={ACTION_TONE[row.action] ?? 'neutral'} />
                  <Tag label={labelFor(OUTCOME_LABEL, row.outcome)} tone={OUTCOME_TONE[row.outcome] ?? 'neutral'} />
                  <Tag label={row.is_simulated ? 'SIMULATED' : 'REAL'} tone={row.is_simulated ? 'simulated' : 'recovered'} />
                </div>
                <p className="mt-2 text-sm text-ink">{row.rationale}</p>
                <p className="mt-2 text-xs text-muted">
                  {labelFor(RULE_LABEL, row.rule_fired)} · cause via {row.cause_source} ·{' '}
                  {formatCount(row.llm_calls_used)} LLM calls · {formatLatency(row.latency_ms)} ·{' '}
                  {formatTimestamp(row.created_at)}
                </p>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
