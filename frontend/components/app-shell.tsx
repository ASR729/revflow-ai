'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, type ReactNode } from 'react';
import { ToastProvider } from '@/components/ui/toaster';
import { RunBatchControl } from '@/components/run-batch';

const NAV = [
  { href: '/', label: 'Overview' },
  { href: '/audit', label: 'Audit Trail' },
  { href: '/exceptions', label: 'Exceptions' },
  { href: '/events', label: 'Events' },
  { href: '/config', label: 'Config' },
  { href: '/settings', label: 'Settings' },
];

function isActive(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  if (href === '/') return pathname === '/';
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <>
      {NAV.map((item) => {
        const active = isActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? 'page' : undefined}
            className={`rounded-card px-3 py-1.5 text-sm transition-colors duration-150 ${
              active
                ? 'bg-navy/10 font-semibold text-navy'
                : 'text-muted hover:bg-surface-2 hover:text-ink'
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <ToastProvider>
      <div className="min-h-screen">
        <header className="sticky top-0 z-40 border-b border-edge bg-surface/90 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-2" aria-label="RevFlow AI home">
                <span
                  aria-hidden="true"
                  className="flex h-7 w-7 items-center justify-center rounded-card bg-navy text-xs font-bold text-surface shadow-card"
                >
                  R
                </span>
                <span className="font-display text-lg font-semibold tracking-tight text-ink">
                  RevFlow <span className="text-navy">AI</span>
                </span>
              </Link>
              <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
                <NavLinks />
              </nav>
            </div>
            <div className="flex items-center gap-2">
              <div className="hidden sm:block">
                <RunBatchControl />
              </div>
              <button
                type="button"
                className="btn-ghost md:hidden"
                aria-expanded={menuOpen}
                aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
                onClick={() => setMenuOpen((v) => !v)}
              >
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                  <path
                    d="M2 4.5h14M2 9h14M2 13.5h14"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>
          </div>
          {menuOpen ? (
            <nav
              className="border-t border-edge bg-surface px-4 py-2 md:hidden"
              aria-label="Primary mobile"
            >
              <div className="flex flex-col gap-1 pb-2">
                <NavLinks onNavigate={() => setMenuOpen(false)} />
                <div className="pt-2">
                  <RunBatchControl />
                </div>
              </div>
            </nav>
          ) : null}
        </header>
        <main id="main" className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
          {children}
        </main>
        <footer className="border-t border-edge py-6">
          <p className="mx-auto max-w-7xl px-4 text-xs text-muted sm:px-6">
            RevFlow AI — payment recovery orchestration. Razorpay Test Mode only; outreach is simulated and never sent.
          </p>
        </footer>
      </div>
    </ToastProvider>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        {description ? <p className="mt-1 max-w-2xl text-sm text-muted">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
