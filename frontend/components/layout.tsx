'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  ListChecks,
  AlertTriangle,
  Settings,
  ChevronRight,
  Menu,
  X,
  BarChart3,
  AlertCircle,
  FileText,
  Settings as SettingsIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatStatus, formatAction } from '@/lib/format';
import { useState } from 'react';

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Audit Trail', href: '/audit', icon: ListChecks },
  { name: 'Exceptions', href: '/exceptions', icon: AlertTriangle },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const pathname = usePathname();

  return (
    <>
      <div
        className={cn(
          'fixed inset-0 z-40 bg-background/80 backdrop-blur-sm',
          'transition-opacity duration-200',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-surface border-r border-border',
          'transform transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-border">
            <Link href="/" className="flex items-center gap-2 font-bold text-lg text-text-primary">
              <svg className="w-8 h-8 text-primary-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
              <span>RevFlow</span>
            </Link>
            <button
              onClick={onClose}
              className="lg:hidden p-2 rounded-md text-text-muted hover:bg-surface-muted"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" role="navigation" aria-label="Main navigation">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-text-secondary hover:bg-surface-muted hover:text-text-primary'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <item.icon className="w-5 h-5" aria-hidden="true" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-border">
            <div className="text-xs text-text-muted">
              RevFlow v0.1.0
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

export function Header({ onMenuClick }: { onMenuClick: () => void }) {
  return (
    <header className="sticky top-0 z-30 h-16 bg-surface/80 backdrop-blur-sm border-b border-border">
      <div className="flex items-center justify-between h-full px-4 md:px-6">
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md text-text-secondary hover:bg-surface-muted"
            aria-label="Open menu"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="hidden md:flex items-center gap-4">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-surface-muted text-sm text-text-muted">
              <span className="font-medium">RevFlow</span>
              <span className="text-text-muted">AI Revenue Recovery</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-muted text-sm text-text-secondary">
            <span className="font-medium">RevFlow</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export function PageLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 h-16 bg-surface/80 backdrop-blur-sm border-b border-border">
          <div className="flex items-center justify-between h-full px-4 md:px-6">
            <div className="flex items-center gap-4">
              <button
                className="lg:hidden p-2 rounded-md text-text-secondary hover:bg-surface-muted"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open menu"
              >
                <Menu className="w-6 h-6" />
              </button>
              <div className="hidden md:flex items-center gap-4">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-surface-muted text-sm text-text-muted">
                  <span className="font-medium">RevFlow</span>
                  <span className="text-text-muted">AI Revenue Recovery</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-muted text-sm text-text-secondary">
                <span className="font-medium">RevFlow</span>
              </div>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}