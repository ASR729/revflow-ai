'use client';

import { useEffect, useRef, useState } from 'react';
import { api, type EventDetailResponse } from '@/lib/api';
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

/**
 * Accessible slide-in event detail drawer.
 * Focus trap + Escape-to-close + focus return to the invoking element.
 */
export function EventDrawer({
  eventId,
  onClose,
}: {
  eventId: string | null;
  onClose: () => void;
}) {
  const [state, setState] = useState<
    { status: 'idle' | 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: EventDetailResponse }
  >({ status: 'idle' });
  const panelRef = useRef<HTMLDivElement | null>(null);
  const restoreRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!eventId) {
      setState({ status: 'idle' });
      return;
    }
    restoreRef.current = document.activeElement as HTMLElement | null;
    setState({ status: 'loading' });
    let cancelled = false;
    api
      .getEventDetail(eventId)
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: 'error',
            message: err instanceof Error ? err.message : 'Unable to load event detail.',
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [eventId]);

  useEffect(() => {
    if (!eventId) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== 'Tab' || !panelRef.current) return;
      const focusables = panelRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKey);
    const t = window.setTimeout(() => {
      panelRef.current?.querySelector<HTMLElement>('button, a[href]')?.focus();
    }, 0);

    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = previousOverflow;
      window.clearTimeout(t);
      restoreRef.current?.focus?.();
    };
  }, [eventId, onClose]);

  if (!eventId) return null;

  const detail = state.status === 'ready' ? state.data : null;

  return (
    <div className="fixed inset-0 z-50" role="presentation">
      <button
        type="button"
        aria-label="Close event detail"
        className="absolute inset-0 h-full w-full bg-ink/40"
        onClick={onClose}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={`Event ${eventId} detail`}
        className="absolute inset-y-0 right-0 flex w-full max-w-lg flex-col border-l border-edge bg-surface shadow-pop motion-safe:transition-transform motion-safe:duration-200 motion-safe:ease-smooth"
      >
        <div className="flex items-center justify-between border-b border-edge px-5 py-4">
          <div>
            <p className="eyebrow">Event detail</p>
            <p className="mt-0.5 font-mono text-sm font-semibold text-ink">{eventId}</p>
          </div>
          <button type="button" className="btn-ghost" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {state.status === 'loading' ? (
            <div className="space-y-3" aria-busy="true" aria-label="Loading event detail">
              <div className="skeleton h-24 w-full" />
              <div className="skeleton h-40 w-full" />
            </div>
          ) : state.status === 'error' ? (
            <div role="alert" className="card border-stopped/30 p-4">
              <p className="text-sm font-semibold text-stopped">Event detail unavailable.</p>
              <p className="mt-1 text-sm text-muted">{state.message}</p>
            </div>
          ) : detail ? (
            <DrawerBody detail={detail} />
          ) : null}
        </div>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="text-right text-sm text-ink">{children}</dd>
    </div>
  );
}

function DrawerBody({ detail }: { detail: EventDetailResponse }) {
  const ev = detail.event;
  return (
    <div className="space-y-5">
      <section aria-label="Event summary" className="card p-4">
        <dl>
          <Row label="Event type">{labelFor(EVENT_TYPE_LABEL, ev.event_type)}</Row>
          <Row label="Amount">
            <span className="font-mono">{formatINRLedger(ev.amount_inr)}</span>
          </Row>
          <Row label="Customer">
            <span className="font-mono">{ev.customer_id}</span>
          </Row>
          <Row label="Decline code">{ev.decline_code ?? '—'}</Row>
          <Row label="Ladder step">
            <Tag label={labelFor(LADDER_LABEL, ev.ladder_step)} tone={LADDER_TONE[ev.ladder_step] ?? 'neutral'} />
          </Row>
          <Row label="Recorded">{formatTimestamp(ev.created_at)}</Row>
        </dl>
      </section>

      <section aria-label="Decision timeline">
        <h3 className="eyebrow mb-2">Decision timeline</h3>
        {detail.timeline.length === 0 ? (
          <p className="text-sm text-muted">No audit entries for this event.</p>
        ) : (
          <ol className="space-y-3">
            {detail.timeline.map((row) => (
              <li key={row.id} className="card p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Tag label={labelFor(ACTION_LABEL, row.action)} tone={ACTION_TONE[row.action] ?? 'neutral'} />
                  <Tag label={labelFor(OUTCOME_LABEL, row.outcome)} tone={OUTCOME_TONE[row.outcome] ?? 'neutral'} />
                  <Tag
                    label={row.is_simulated ? 'SIMULATED' : 'REAL'}
                    tone={row.is_simulated ? 'simulated' : 'recovered'}
                  />
                </div>
                <p className="mt-2 text-sm text-ink">{row.rationale}</p>
                <dl className="mt-3 grid grid-cols-2 gap-x-4">
                  <Row label="Rule fired">{labelFor(RULE_LABEL, row.rule_fired)}</Row>
                  <Row label="Cause source">{row.cause_source}</Row>
                  <Row label="LLM calls">{formatCount(row.llm_calls_used)}</Row>
                  <Row label="Latency">{formatLatency(row.latency_ms)}</Row>
                  <Row label="Amount">
                    <span className="font-mono">{formatINRLedger(row.amount_inr)}</span>
                  </Row>
                  <Row label="Time">{formatTimestamp(row.created_at)}</Row>
                </dl>
              </li>
            ))}
          </ol>
        )}
      </section>

      {detail.simulated_actions.length > 0 ? (
        <section aria-label="Simulated outreach">
          <h3 className="eyebrow mb-2">Simulated outreach</h3>
          <ul className="space-y-2">
            {detail.simulated_actions.map((s) => (
              <li key={s.id} className="card p-4">
                <div className="flex items-center gap-2">
                  <Tag label="SIMULATED" tone="simulated" />
                  <span className="text-xs uppercase tracking-wide text-muted">{s.channel}</span>
                </div>
                <p className="mt-2 text-sm text-ink">{s.body_text}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {detail.escalations.length > 0 ? (
        <section aria-label="Escalations">
          <h3 className="eyebrow mb-2">Escalations</h3>
          <ul className="space-y-2">
            {detail.escalations.map((e) => (
              <li key={e.id} className="card p-4">
                <p className="text-sm text-ink">{e.reason}</p>
                <p className="mt-1 text-xs text-muted">
                  Queue: {e.queue} · Step: {labelFor(LADDER_LABEL, e.ladder_step)} · {formatTimestamp(e.created_at)}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {detail.ptp_commitments.length > 0 ? (
        <section aria-label="Promise to pay">
          <h3 className="eyebrow mb-2">Promise to pay</h3>
          <ul className="space-y-2">
            {detail.ptp_commitments.map((p) => (
              <li key={p.id} className="card p-4">
                <div className="flex items-center gap-2">
                  <Tag
                    label={p.status}
                    tone={p.status === 'kept' ? 'recovered' : p.status === 'broken' ? 'stopped' : 'atrisk'}
                  />
                  <span className="text-xs text-muted">Promised {formatTimestamp(p.promised_date)}</span>
                </div>
                {p.detected_from_text ? (
                  <p className="mt-2 text-sm text-ink">“{p.detected_from_text}”</p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
