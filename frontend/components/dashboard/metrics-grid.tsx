'use client';

import { cn } from '@/lib/utils';
import { formatAmountDisplay, formatRate, formatPercentage, displayValue } from '@/lib/format';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number | null;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: React.ReactNode;
  className?: string;
}

function MetricCard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  className,
}: MetricCardProps) {
  const trendIcons = {
    up: <TrendingUp className="w-4 h-4 text-success-600" />,
    down: <TrendingDown className="w-4 h-4 text-danger-600" />,
    neutral: <Minus className="w-4 h-4 text-text-muted" />,
  };

  const trendColors = {
    up: 'text-success-600',
    down: 'text-danger-600',
    neutral: 'text-text-muted',
  };

  return (
    <div className={`card p-6 ${className || ''}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text-secondary">{title}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-text-primary tabular-nums">
              {typeof value === 'string' ? value : value !== null && value !== undefined ? String(value) : '—'}
            </span>
            {trend && trendValue && (
              <span className={cn('text-sm font-medium', trendColors[trend])}>
                {trendIcons[trend]} {trendValue}
              </span>
            )}
          </div>
          {subtitle && <p className="mt-1 text-sm text-text-muted">{subtitle}</p>}
        </div>
        <div className="ml-4 flex-shrink-0">
          {icon}
        </div>
      </div>
    </div>
  );
}

interface MetricsGridProps {}

export function MetricsGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        title="At Risk"
        value="₹69.33L"
        subtitle="Total amount at risk"
        icon={
          <svg className="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        }
        trend="neutral"
      />
      <MetricCard
        title="Addressable"
        value="₹2.34L"
        subtitle="Amount addressable for recovery"
        icon={
          <svg className="w-8 h-8 text-info-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2V8a2 2 0 012-2h6a2 2 0 012 2v11.5a.5.5 0 00.5.5h2a.5.5 0 00.5-.5z" />
          </svg>
        }
        trend="neutral"
      />
      <MetricCard
        title="Recovered"
        value="₹1.39L"
        subtitle="Successfully recovered"
        icon={
          <svg className="w-8 h-8 text-success-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
        trend="up"
        trendValue="+12%"
      />
      <MetricCard
        title="Recovery Rate"
        value="36.3%"
        subtitle="Overall recovery rate"
        icon={
          <svg className="w-8 h-8 text-success-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        }
        trend="up"
        trendValue="+2.1%"
      />
    </div>
  );
}