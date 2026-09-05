'use client';

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

type ToastKind = 'success' | 'error' | 'info' | 'warning';

interface ToastItem {
  id: number;
  kind: ToastKind;
  title: string;
  message?: string;
}

interface ToastApi {
  push: (kind: ToastKind, title: string, message?: string) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>');
  return ctx;
}

const KIND_CLASS: Record<ToastKind, string> = {
  success: 'border-recovered/40',
  error: 'border-stopped/40',
  info: 'border-navy/40',
  warning: 'border-atrisk/40',
};

const KIND_TITLE: Record<ToastKind, string> = {
  success: 'text-recovered',
  error: 'text-stopped',
  info: 'text-navy',
  warning: 'text-atrisk',
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const push = useCallback((kind: ToastKind, title: string, message?: string) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, kind, title, message }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 6000);
  }, []);

  const api = useMemo(() => ({ push }), [push]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`pointer-events-auto card border-l-4 ${KIND_CLASS[t.kind]} px-4 py-3 shadow-pop`}
          >
            <p className={`text-sm font-semibold ${KIND_TITLE[t.kind]}`}>{t.title}</p>
            {t.message ? <p className="mt-0.5 text-xs text-muted">{t.message}</p> : null}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
