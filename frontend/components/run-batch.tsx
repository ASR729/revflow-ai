'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import type { BatchRunRow } from '@/lib/api';
import { useToast } from '@/components/ui/toaster';

const POLL_MS = 3000;

/**
 * Run Batch control (the only non-GET interaction, per contract).
 * POST /run-batch -> 202 { run_id, status: 'running', poll: '/runs' }
 * then polls GET /runs until the run leaves 'running', refreshes all screens.
 */
export function RunBatchControl() {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [useLlm, setUseLlm] = useState(false);
  const [regenerate, setRegenerate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [activeRun, setActiveRun] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]);

  const finish = useCallback(
    (run: BatchRunRow) => {
      stopPolling();
      setActiveRun(null);
      if (run.status === 'completed') {
        toast.push('success', 'Batch completed', `Run ${run.run_id} finished. Metrics refreshed.`);
      } else if (run.status === 'failed') {
        toast.push('error', 'Batch failed', `Run ${run.run_id} failed on the backend.`);
      }
      window.dispatchEvent(new Event('revflow:refresh'));
    },
    [stopPolling, toast],
  );

  const poll = useCallback(
    (runId: string) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const runs = await api.listRuns();
          const current = runs.runs.find((r) => r.run_id === runId);
          if (current && current.status !== 'running') finish(current);
        } catch {
          // transient poll failure: keep polling; the UI stays in the running state
        }
      }, POLL_MS);
    },
    [finish, stopPolling],
  );

  const start = useCallback(async () => {
    setBusy(true);
    try {
      const res = await api.runBatch({ use_llm: useLlm, regenerate_dataset: regenerate });
      setOpen(false);
      setActiveRun(res.run_id);
      toast.push('info', 'Batch started', `Run ${res.run_id} is running.`);
      poll(res.run_id);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Run could not be started.';
      const is409 = message.includes('409') || /already running/i.test(message);
      toast.push(
        is409 ? 'warning' : 'error',
        is409 ? 'A batch is already running' : 'Run could not be started',
        is409 ? undefined : message,
      );
    } finally {
      setBusy(false);
    }
  }, [poll, regenerate, toast, useLlm]);

  return (
    <div className="relative">
      {activeRun ? (
        <span
          className="btn-secondary cursor-default"
          role="status"
          aria-live="polite"
          title="Batch in progress"
        >
          <span className="spinner" aria-hidden="true" />
          Running… <span className="font-mono text-xs">{activeRun}</span>
        </span>
      ) : (
        <button type="button" className="btn-primary" onClick={() => setOpen((v) => !v)}>
          Run batch
        </button>
      )}

      {open ? (
        <div
          role="dialog"
          aria-label="Run batch options"
          className="card absolute right-0 top-full z-40 mt-2 w-80 p-4 shadow-pop"
        >
          <p className="text-sm font-semibold text-ink">Start a batch run</p>
          <p className="mt-1 text-xs text-muted">
            Runs the deterministic pipeline by default. The LLM path is opt-in and rate-limited.
          </p>
          <label className="mt-3 flex items-start gap-2 text-sm text-ink">
            <input
              type="checkbox"
              className="mt-0.5"
              checked={useLlm}
              onChange={(e) => setUseLlm(e.target.checked)}
            />
            <span>
              Use LLM classification
              <span className="block text-xs text-muted">
                {useLlm ? 'Live LLM calls will be used.' : 'Off — deterministic rules only (recommended for demo).'}
              </span>
            </span>
          </label>
          <label className="mt-2 flex items-start gap-2 text-sm text-ink">
            <input
              type="checkbox"
              className="mt-0.5"
              checked={regenerate}
              onChange={(e) => setRegenerate(e.target.checked)}
            />
            <span>
              Regenerate dataset
              <span className="block text-xs text-muted">Rebuild the synthetic event set before processing.</span>
            </span>
          </label>
          <div className="mt-4 flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setOpen(false)}>
              Cancel
            </button>
            <button type="button" className="btn-primary" disabled={busy} onClick={start}>
              {busy ? 'Starting…' : 'Start run'}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
