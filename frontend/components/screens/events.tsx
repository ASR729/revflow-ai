'use client';

import { useState } from 'react';
import { api, type AuditLogResponse } from '@/lib/api';
import { useApiData } from '@/lib/use-api-data';
import { PageHeader } from '@/components/app-shell';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/ui/states';
import { Tag } from '@/components/ui/badge';
import { EventDrawer } from '@/components/event-drawer';
import { ACTION_LABEL, ACTION_TONE, EVENT_TYPE_LABEL, OUTCOME_LABEL, OUTCOME_TONE, labelFor } from '@/lib/labels';
import { formatINRLedger, formatTimestamp } from '@/lib/format';

/**
 * Events list sourced from the typed API client's audit log (the contract has
 * no GET /events list endpoint; individual detail comes from /events/{id}).
 */
export function EventsScreen() {
  const state = useApiData<AuditLogResponse>(() => api.getAuditLog({ limit: 500, sort: 'timestamp', order: 'desc' }));
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div>
      <PageHeader
        title="Events"
        description="Every event the pipeline touched. Select one for its full decision detail."
      />

      <div className="card mb-4 p-4">
        <label className="text-xs font-medium text-muted">
          Search events
          <input
            type="search"
            className="input mt-1 max-w-md"
            placeholder="Filter by event ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>

      {state.status === 'loading' ? (
        <TableSkeleton />
      ) : state.status === 'error' ? (
        <ErrorState title="Unable to load events." message={state.message} />
      ) : (
        <EventsTable data={state.data} search={search} onSelect={setSelected} />
      )}

      <EventDrawer eventId={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function EventsTable({
  data,
  search,
  onSelect,
}: {
  data: AuditLogResponse;
  search: string;
  onSelect: (eventId: string) => void;
}) {
  const seen = new Set<string>();
  const uniqueRows = data.rows.filter((r) => {
    if (seen.has(r.event_id)) return false;
    seen.add(r.event_id);
    return true;
  });

  const needle = search.trim().toLowerCase();
  const rows = needle ? uniqueRows.filter((r) => r.event_id.toLowerCase().includes(needle)) : uniqueRows;

  if (rows.length === 0) {
    return <EmptyState title="No events available" description="Run a batch to populate the event ledger." />;
  }

  return (
    <div className="card table-shell">
      <table className="table">
        <caption className="sr-only">Events processed in the latest run</caption>
        <thead>
          <tr>
            <th scope="col">Event ID</th>
            <th scope="col">Pipeline</th>
            <th scope="col">Action</th>
            <th scope="col">Outcome</th>
            <th scope="col" className="text-right">Amount</th>
            <th scope="col">Time</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.event_id}>
              <td>
                <button
                  type="button"
                  className="font-mono text-xs text-navy underline-offset-2 hover:underline"
                  onClick={() => onSelect(row.event_id)}
                >
                  {row.event_id}
                </button>
              </td>
              <td className="text-sm">{labelFor(EVENT_TYPE_LABEL, row.event_type)}</td>
              <td>
                <Tag label={labelFor(ACTION_LABEL, row.action)} tone={ACTION_TONE[row.action] ?? 'neutral'} />
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
  );
}
