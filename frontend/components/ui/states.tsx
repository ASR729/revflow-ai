import type { ReactNode } from 'react';

export function PageSkeleton({ rows = 4 }: { rows?: number }) {
  const keys = Array.from({ length: rows }, (_, i) => `sk-${i}`);
  return (
    <div className="space-y-4" aria-busy="true" aria-label="Loading">
      {keys.map((k) => (
        <div key={k} className="card p-5">
          <div className="skeleton h-4 w-1/4" />
          <div className="skeleton mt-3 h-4 w-2/3" />
          <div className="skeleton mt-2 h-4 w-1/2" />
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 8 }: { rows?: number }) {
  const keys = Array.from({ length: rows }, (_, i) => `skr-${i}`);
  return (
    <div className="card p-4" aria-busy="true" aria-label="Loading table">
      <div className="skeleton h-4 w-1/3" />
      <div className="mt-4 space-y-3">
        {keys.map((k) => (
          <div key={k} className="skeleton h-5 w-full" />
        ))}
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-2" aria-hidden="true">
        <span className="h-2 w-2 rounded-full bg-muted" />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-ink">{title}</h3>
      {description ? <p className="mt-1 max-w-sm text-sm text-muted">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ title, message }: { title: string; message?: string }) {
  return (
    <div className="card border-stopped/30 px-6 py-10 text-center" role="alert">
      <p className="text-sm font-semibold text-stopped">{title}</p>
      <p className="mt-1 text-sm text-muted">
        {message ?? 'Unable to reach the RevFlow backend. Start the API server and reload this page.'}
      </p>
    </div>
  );
}
