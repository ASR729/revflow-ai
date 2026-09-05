'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { PageHeader } from '@/components/app-shell';
import { Tag } from '@/components/ui/badge';

/**
 * Single-event ingestion via the real POST /webhook endpoint.
 */
export function WebhookScreen() {
  const [payload, setPayload] = useState('{\n  "event": "",\n  "payload": {}\n}');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<
    | { kind: 'idle' }
    | { kind: 'accepted'; eventId: string; runId: string }
    | { kind: 'error'; message: string }
  >({ kind: 'idle' });

  const submit = async () => {
    setBusy(true);
    setResult({ kind: 'idle' });
    try {
      const parsed = JSON.parse(payload) as { event?: string; payload?: unknown };
      if (!parsed.event || typeof parsed.event !== 'string') {
        setResult({ kind: 'error', message: 'Payload must include a string "event" field.' });
        return;
      }
      const res = await api.postWebhook({
        event: parsed.event,
        payload: (parsed.payload ?? {}) as Record<string, unknown>,
      });
      setResult({ kind: 'accepted', eventId: res.event_id, runId: res.run_id });
      window.dispatchEvent(new Event('revflow:refresh'));
    } catch (err) {
      setResult({
        kind: 'error',
        message: err instanceof Error ? err.message : 'Webhook rejected by the backend.',
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Webhook"
        description="Ingest a single event straight into the pipeline via POST /webhook."
      />
      <section className="card max-w-2xl p-5" aria-label="Webhook submission">
        <label className="block text-sm font-medium text-ink">
          Request body (JSON)
          <textarea
            className="input mt-2 h-48 font-mono text-xs"
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            spellCheck={false}
            aria-label="Webhook JSON payload"
          />
        </label>
        <div className="mt-4 flex items-center gap-3">
          <button type="button" className="btn-primary" onClick={submit} disabled={busy}>
            {busy ? 'Sending…' : 'Send webhook'}
          </button>
          {result.kind === 'accepted' ? (
            <Tag label={`Accepted — ${result.eventId} (${result.runId})`} tone="recovered" />
          ) : result.kind === 'error' ? (
            <p role="alert" className="text-sm text-stopped">{result.message}</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}
