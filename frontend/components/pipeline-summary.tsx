'use client';

import { cn } from '@/lib/utils';
import { formatAmountDisplay, formatRate, displayValue } from '@/lib/format';
import { formatStatus, formatAction, formatLadderStep } from '@/lib/format';

interface PipelineSummaryProps {}

export function PipelineSummary() {
  // Pipeline stages based on the action table
  const stages = [
    { key: 'retry_now', label: 'Retry Now', color: 'info', action: 'retry_now' },
    { key: 'retry_later', label: 'Retry Later', color: 'warning', action: 'retry_later' },
    { key: 'nudge', label: 'Nudge', color: 'info', action: 'nudge' },
    { key: 'escalate_to_human', label: 'Escalate', color: 'warning', action: 'escalate_to_human' },
    { key: 'stop', label: 'Stop', color: 'danger', action: 'stop' },
  ];

  // These would come from the API in a real implementation
  const stageData = [
    { key: 'retry_now', count: 40, amount: 19632184 },
    { key: 'retry_later', count: 205, amount: 129510539 },
    { key: 'nudge', count: 40, amount: 14436301 },
    { key: 'escalate_to_human', count: 111, amount: 202037163 },
    { key: 'stop', count: 17, amount: 80122504 },
  ];

  const totalEvents = 300;
  const totalAmount = 693292936;

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">Pipeline Summary</h2>
          <p className="text-sm text-text-muted mt-1">Action distribution across recovery pipeline</p>
        </div>
        <div className="flex items-center gap-4 text-sm text-text-muted">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-info-500" />
            <span className="text-xs text-text-muted">Events</span>
          </span>
          <span className="w-px h-4 bg-border mx-2" />
          <span className="font-medium text-text-primary">{totalEvents}</span>
          <span className="text-text-muted">Total Events</span>
        </div>
      </div>

      {/* Pipeline Flow */}
      <div className="space-y-4">
        {/* Pipeline Steps */}
        <div className="relative">
          {/* Connecting line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-border -translate-x-1/2 hidden lg:block" />
          
          <div className="flex flex-col lg:flex-row items-center gap-4 lg:gap-2">
            {[
              { key: 'retry_now', label: 'Retry Now', count: 40, amount: 19632184, color: 'info', action: 'retry_now' },
              { key: 'retry_later', label: 'Retry Later', count: 205, amount: 129510539, color: 'warning', action: 'retry_later' },
              { key: 'nudge', label: 'Nudge', count: 40, amount: 14436301, color: 'info', action: 'nudge' },
              { key: 'escalate_to_human', label: 'Escalate', count: 111, amount: 202037163, color: 'warning', action: 'escalate_to_human' },
              { key: 'stop', label: 'Stop', count: 17, amount: 80122504, color: 'danger', action: 'stop' },
            ].map((stage, index) => (
              <div key={stage.key} className="flex flex-col items-center flex-1 relative z-10">
                {/* Node */}
                <div className="flex flex-col items-center">
                  <div className={cn(
                    'w-16 h-16 rounded-full flex items-center justify-center shadow-lg border-4 border-white',
                    `bg-${stage.color}-100 text-${stage.color}-600`
                  )}>
                    <span className="font-semibold text-sm">{stage.count}</span>
                  </div>
                  <p className="mt-2 text-sm font-medium text-text-primary text-center">{stage.label}</p>
                  <p className="text-xs text-text-muted mt-0.5">
                    ₹{(stage.amount / 100000).toFixed(1)}L
                  </p>
                </div>
                {/* Connector */}
                {index < 4 && (
                  <div className="hidden lg:block w-16 h-px bg-border mt-8" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Pipeline Summary Stats */}
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {[
            { label: 'Total Events', value: '300', icon: '📊' },
            { label: 'Total Amount', value: '₹69.33L', icon: '💰' },
            { label: 'Recovered', value: '₹1.39L', icon: '✅' },
            { label: 'Recovery Rate', value: '36.3%', icon: '📈' },
            { label: 'Recovery Rate', value: '36.3%', icon: '📈' },
          ].map((stat, index) => (
            <div key={stat.label} className="card p-4 text-center">
              <p className="text-2xl font-bold text-text-primary">{stat.value}</p>
              <p className="text-sm text-text-muted mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}