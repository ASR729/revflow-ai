'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export type AsyncState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: T };

/**
 * Shared typed-data hook. Every screen subscribes to 'revflow:refresh'
 * so a completed batch run re-pulls real data without a page reload.
 */
export function useApiData<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<AsyncState<T>>({ status: 'loading' });
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const load = useCallback(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    loaderRef.current()
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: 'error',
            message: err instanceof Error ? err.message : 'Unable to reach the RevFlow backend.',
          });
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => load(), [load]);

  useEffect(() => {
    const handler = () => load();
    window.addEventListener('revflow:refresh', handler);
    return () => window.removeEventListener('revflow:refresh', handler);
  }, [load]);

  return state;
}
