'use client';

import { useState } from 'react';
import { api, type ExceptionRow, type ExceptionsResponse } from '@/lib/api';
import { useApiData } from '@/lib/use-api-data';
import { PageHeader } from '@/components/app-shell';
import { EmptyState, ErrorState, PageSkeleton } from '@/components/ui/states';
import { Tag } from '@/components/ui/badge';
import { EventDrawer } from '@/components/event-drawer';
import { CAUSE_LABEL, EVENT_TYPE_LABEL, RULE_LABEL, labelFor } from '@/lib/labels';
import { formatCount, formatINRLedger } from '@/lib/format';

export function ExceptionsScreen() {
  const state = useApiData<ExceptionsResponse>(() => api.getExceptions());
  const [selected, setSelected] = useState<string | null>(null);
  const [reviewed, setReviewed] = useState<Set<number>>(new Set());

  const markReviewed = (id: number) =>
    setReviewed((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });

  const total =
    state.status === 'ready'
      ? state.data.withheld_by_policy.length + state.data.needs_a_human.length
      : 0;

  return (
    <div>
      <PageHeader
        title="Exceptions"
        description="Events the policy engine refused to touch, or deliberately handed to a human."
      />

      {state.status === 'loading' ? (
        <PageSkeleton rows={3} />
      ) : state.status === 'error' ? (
        <ErrorState title="Unable to load exceptions." message={state.message} />
      ) : total === 0 ? (
        <EmptyState
          title="No exceptions for this run"
          description="Nothing was withheld and nothing needs a human. The policy engine handled every event."
        />
      ) : (
        <div className="space-y-6">
          <ExceptionGroup
            title="Withheld by policy"
            rows={state.data.withheld_by_policy}
            reviewed={reviewed}
            onReviewed={markReviewed}
            onOpen={setSelected}
          />
          <ExceptionGroup
            title="Needs a human"
            rows={state.data.needs_a_human}
            reviewed={reviewed}
            onReviewed={markReviewed}
            onOpen={setSelected}
          />
        </div>
      )}

      <EventDrawer eventId={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function ExceptionGroup({
  title,
  rows,
  reviewed,
  onReviewed,
  onOpen,
}: {
  title: string;
  rows: ExceptionRow[];
  reviewed: Set<number>;
  onReviewed: (id: number) => void;
  onOpen: (eventId: string) => void;
}) {
  return (
    <section aria-label={title}>
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
        <span className="text-xs text-muted">{formatCount(rows.length)} events</span>
      </div>
      {rows.length === 0 ? (
        <EmptyState title={`Nothing in “${title}”`} />
      ) : (
        <div className="card table-shell">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Event</th>
                <th scope="col">Pipeline</th>
                <th scope="col">Cause</th>
                <th scope="col">Rule</th>
                <th scope="col" className="text-right">Amount</th>
                <th scope="col" className="text-right">Review</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const isReviewed = reviewed.has(row.id);
                return (
                  <tr key={row.id} className={isReviewed ? 'opacity-50' : undefined}>
                    <td>
                      <button
                        type="button"
                        className="font-mono text-xs text-navy underline-offset-2 hover:underline"
                        onClick={() => onOpen(row.event_id)}
                      >
                        {row.event_id}
                      </button>
                    </td>
                    <td className="text-sm">{labelFor(EVENT_TYPE_LABEL, row.event_type)}</td>
                    <td className="text-sm">{labelFor(CAUSE_LABEL, row.cause)}</td>
                    <td className="text-sm">{labelFor(RULE_LABEL, row.rule_fired)}</td>
                    <td className="text-right font-mono text-sm tabular-nums">
                      {formatINRLedger(row.amount_inr)}
                    </td>
                    <td className="text-right">
                      {isReviewed ? (
                        <Tag label="Reviewed" tone="recovered" />
                      ) : (
                        <button
                          type="button"
                          className="btn-secondary px-2.5 py-1 text-xs"
                          onClick={() => onReviewed(row.id)}
                          aria-label={`Mark ${row.event_id} as reviewed (local only)`}
                          title="Session state only — no request is sent"
                        >
                          Mark reviewed
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
