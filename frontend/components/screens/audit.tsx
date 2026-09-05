'use client';

import { useMemo, useState } from 'react';
import { api, type AuditLogQuery, type AuditLogResponse } from '@/lib/api';
import { useApiData } from '@/lib/use-api-data';
import { PageHeader } from '@/components/app-shell';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/ui/states';
import { Tag } from '@/components/ui/badge';
import { EventDrawer } from '@/components/event-drawer';
import {
  ACTION_LABEL,
  ACTION_TONE,
  CAUSE_LABEL,
  EVENT_TYPE_LABEL,
  OUTCOME_LABEL,
  OUTCOME_TONE,
  RULE_LABEL,
  labelFor,
} from '@/lib/labels';
import { formatCount, formatINRLedger, formatTimestamp } from '@/lib/format';

const EVENT_TYPES = ['', 'checkout_dropoff', 'subscription_failure', 'b2b_receivable'];
const CAUSES = [
  '',
  'insufficient_funds',
  'bank_timeout',
  'technical_decline',
  'business_decline',
  'authentication_failed',
  'session_timeout',
  'user_abandoned',
  'mandate_expired',
  'user_revoked',
  'invoice_overdue',
  'invoice_disputed',
  'awaiting_po',
  'unclassified',
];
const ACTIONS = ['', 'retry_now', 'retry_later', 'nudge', 'escalate_to_human', 'stop'];

export function AuditScreen() {
  const [eventType, setEventType] = useState('');
  const [cause, setCause] = useState('');
  const [action, setAction] = useState('');
  const [sort, setSort] = useState<NonNullable<AuditLogQuery['sort']>>('timestamp');
  const [order, setOrder] = useState<NonNullable<AuditLogQuery['order']>>('desc');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string | null>(null);

  const query = useMemo<AuditLogQuery>(
    () => ({
      event_type: eventType || undefined,
      cause: cause || undefined,
      action: action || undefined,
      sort,
      order,
      limit: 200,
    }),
    [eventType, cause, action, sort, order],
  );

  const state = useApiData<AuditLogResponse>(() => api.getAuditLog(query), [query]);

  return (
    <div>
      <PageHeader
        title="Audit Trail"
        description="Every decision the agent made, with rule, rationale, and outcome."
      />

      <form
        className="card mb-4 grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-6"
        aria-label="Audit filters"
        onSubmit={(e) => e.preventDefault()}
      >
        <label className="text-xs font-medium text-muted">
          Event ID
          <input
            className="input mt-1"
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search event ID"
          />
        </label>
        <label className="text-xs font-medium text-muted">
          Pipeline
          <select className="input mt-1" value={eventType} onChange={(e) => setEventType(e.target.value)}>
            {EVENT_TYPES.map((v) => (
              <option key={v || 'all'} value={v}>
                {v ? labelFor(EVENT_TYPE_LABEL, v) : 'All pipelines'}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-medium text-muted">
          Cause
          <select className="input mt-1" value={cause} onChange={(e) => setCause(e.target.value)}>
            {CAUSES.map((v) => (
              <option key={v || 'all'} value={v}>
                {v ? labelFor(CAUSE_LABEL, v) : 'All causes'}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-medium text-muted">
          Action
          <select className="input mt-1" value={action} onChange={(e) => setAction(e.target.value)}>
            {ACTIONS.map((v) => (
              <option key={v || 'all'} value={v}>
                {v ? labelFor(ACTION_LABEL, v) : 'All actions'}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-medium text-muted">
          Sort by
          <select
            className="input mt-1"
            value={sort}
            onChange={(e) => setSort(e.target.value as NonNullable<AuditLogQuery['sort']>)}
          >
            <option value="timestamp">Timestamp</option>
            <option value="amount">Amount</option>
            <option value="cause">Cause</option>
          </select>
        </label>
        <label className="text-xs font-medium text-muted">
          Order
          <select
            className="input mt-1"
            value={order}
            onChange={(e) => setOrder(e.target.value as NonNullable<AuditLogQuery['order']>)}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
      </form>

      {state.status === 'loading' ? (
        <TableSkeleton />
      ) : state.status === 'error' ? (
        <ErrorState title="Unable to load the audit trail." message={state.message} />
      ) : (
        <AuditTable
          data={state.data}
          search={search}
          onSelect={(id) => setSelected(id)}
        />
      )}

      <EventDrawer eventId={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function AuditTable({
  data,
  search,
  onSelect,
}: {
  data: AuditLogResponse;
  search: string;
  onSelect: (eventId: string) => void;
}) {
  const needle = search.trim().toLowerCase();
  const rows = needle
    ? data.rows.filter((r) => r.event_id.toLowerCase().includes(needle))
    : data.rows;

  if (rows.length === 0) {
    return (
      <EmptyState
        title="No audit records found"
        description="No audit rows match the current filters for this run."
      />
    );
  }

  return (
    <>
      <p className="mb-2 text-xs text-muted" aria-live="polite">
        {formatCount(rows.length)} of {formatCount(data.total)} records
      </p>
      <div className="card table-shell">
        <table className="table">
          <caption className="sr-only">Audit log rows for the latest run</caption>
          <thead>
            <tr>
              <th scope="col">Event</th>
              <th scope="col">Pipeline</th>
              <th scope="col">Cause</th>
              <th scope="col">Rule fired</th>
              <th scope="col">Action</th>
              <th scope="col">Outcome</th>
              <th scope="col" className="text-right">Amount</th>
              <th scope="col">Time</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>
                  <button
                    type="button"
                    className="font-mono text-xs text-navy underline-offset-2 hover:underline"
                    onClick={() => onSelect(row.event_id)}
                  >
                    {row.event_id}
                  </button>
                  <div className="mt-1">
                    <Tag
                      label={row.is_simulated ? 'SIMULATED' : 'REAL'}
                      tone={row.is_simulated ? 'simulated' : 'recovered'}
                    />
                  </div>
                </td>
                <td className="text-sm">{labelFor(EVENT_TYPE_LABEL, row.event_type)}</td>
                <td className="text-sm">{labelFor(CAUSE_LABEL, row.cause)}</td>
                <td className="text-sm">{labelFor(RULE_LABEL, row.rule_fired)}</td>
                <td>
                  <Tag label={labelFor(ACTION_LABEL, row.action)} tone={ACTION_TONE[row.action] ?? 'neutral'} />
                  {row.action === 'stop' ? <WithheldStampInline /> : null}
                </td>
                <td>
                  <Tag label={labelFor(OUTCOME_LABEL, row.outcome)} tone={OUTCOME_TONE[row.outcome] ?? 'neutral'} />
                </td>
                <td className="text-right font-mono text-sm tabular-nums">{formatINRLedger(row.amount_inr)}</td>
                <td className="whitespace-nowrap text-xs text-muted">{formatTimestamp(row.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function WithheldStampInline() {
  return (
    <span
      aria-label="Withheld"
      className="ml-2 inline-block -rotate-6 rounded-sm border border-stopped/60 px-1.5 py-0.5 withheld-stamp-text"
    >
      Withheld
    </span>
  );
}
