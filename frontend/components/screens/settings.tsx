'use client';

import { useEffect, useState } from 'react';
import { api, type HealthResponse } from '@/lib/api';
import { PageHeader } from '@/components/app-shell';
import { Tag } from '@/components/ui/badge';

/**
 * Settings is intentionally read-only: the backend exposes no mutation
 * endpoints, so nothing here may pretend to save.
 */
export function SettingsScreen() {
  const [health, setHealth] = useState<
    { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: HealthResponse }
  >({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    api
      .health()
      .then((data) => !cancelled && setHealth({ status: 'ready', data }))
      .catch((err: unknown) => {
        if (!cancelled) {
          setHealth({ status: 'error', message: err instanceof Error ? err.message : 'Unreachable' });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
    ? process.env.NEXT_PUBLIC_API_BASE_URL
    : 'Same-origin proxy (/api → backend)';

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Environment and connectivity. All values are read-only; the backend does not accept configuration changes at runtime."
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="card p-5" aria-label="Backend connectivity">
          <h2 className="eyebrow mb-3">Backend connectivity</h2>
          {health.status === 'loading' ? (
            <div className="space-y-2" aria-busy="true">
              <div className="skeleton h-4 w-2/3" />
              <div className="skeleton h-4 w-1/2" />
            </div>
          ) : health.status === 'error' ? (
            <div role="alert">
              <Tag label="Offline" tone="stopped" />
              <p className="mt-2 text-sm text-muted">{health.message}</p>
            </div>
          ) : (
            <dl className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <Tag label="Healthy" tone="recovered" />
                <span className="text-muted">version {health.data.version}</span>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Database</dt>
                <dd className="font-mono text-xs">{health.data.db}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Razorpay mode</dt>
                <dd>
                  <Tag label={health.data.razorpay_mode} tone="atrisk" />
                </dd>
              </div>
            </dl>
          )}
        </section>

        <section className="card p-5" aria-label="Environment">
          <h2 className="eyebrow mb-3">Environment</h2>
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-muted">API base</dt>
              <dd className="mt-0.5 font-mono text-xs text-ink">{apiBase}</dd>
            </div>
            <div>
              <dt className="text-muted">Write access</dt>
              <dd className="mt-0.5 flex items-center gap-2">
                <Tag label="Read-only" tone="neutral" />
                <span className="text-xs text-muted">Policy changes require a redeploy; nothing here writes back.</span>
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </div>
  );
}
