'use client';

import { cn } from '@/lib/utils';
import { formatDate, formatTime, displayValue } from '@/lib/format';
import { formatStatus, formatAction } from '@/lib/format';

interface RecentActivityProps {}

function getActionBadgeClass(action: string): string {
  switch (action) {
    case 'retry_now':
    case 'nudge':
      return 'bg-info-100 text-info-700';
    case 'retry_later':
    case 'escalate_to_human':
      return 'bg-warning-100 text-warning-700';
    case 'stop':
      return 'bg-danger-100 text-danger-700';
    default:
      return 'bg-surface-muted text-text-muted';
  }
}

function getOutcomeBadgeClass(outcome: string): string {
  switch (outcome) {
    case 'recovered':
      return 'bg-success-100 text-success-700';
    case 'failed':
    case 'withheld':
      return 'bg-danger-100 text-danger-700';
    case 'api_error':
    case 'simulated':
      return 'bg-info-100 text-info-700';
    case 'pending':
    case 'paused':
    case 'escalated':
      return 'bg-warning-100 text-warning-700';
    default:
      return 'bg-surface-muted text-text-muted';
  }
}

function getEventTypeBadgeClass(eventType: string): string {
  switch (eventType) {
    case 'checkout_dropoff':
      return 'bg-info-100 text-info-700';
    case 'subscription_failure':
      return 'bg-warning-100 text-warning-700';
    case 'b2b_receivable':
      return 'bg-success-100 text-success-700';
    default:
      return 'bg-surface-muted text-text-muted';
  }
}

export function RecentActivity() {
  // Sample activity data - in real implementation this would come from API
  const activities = [
    {
      id: '1',
      timestamp: '2026-09-04T13:24:09.000Z',
      eventId: 'EVT-0904110538-0001',
      eventType: 'checkout_dropoff',
      action: 'retry_now',
      outcome: 'recovered',
      amount: 955101,
      customerId: 'CUST-0001',
    },
    {
      id: '2',
      timestamp: '2026-09-04T13:23:45.000Z',
      eventId: 'EVT-0904110538-0025',
      eventType: 'subscription_failure',
      action: 'escalate_to_human',
      outcome: 'escalated',
      amount: 251235,
      customerId: 'CUST-0042',
    },
    {
      id: '3',
      timestamp: '2026-09-04T13:22:12.000Z',
      eventId: 'EVT-0904110538-0087',
      eventType: 'b2b_receivable',
      action: 'nudge',
      outcome: 'simulated',
      amount: 1524150,
      customerId: 'CUST-0123',
    },
    {
      id: '4',
      timestamp: '2026-09-04T13:20:33.000Z',
      eventId: 'EVT-0904110538-0156',
      eventType: 'checkout_dropoff',
      action: 'retry_now',
      outcome: 'recovered',
      amount: 789500,
      customerId: 'CUST-0089',
    },
    {
      id: '5',
      timestamp: '2026-09-04T13:19:01.000Z',
      eventId: 'EVT-0904110538-0203',
      eventType: 'b2b_receivable',
      action: 'escalate_to_human',
      outcome: 'escalated',
      amount: 2541000,
      customerId: 'CUST-0456',
    },
    {
      id: '6',
      timestamp: '2026-09-04T13:17:45.000Z',
      eventId: 'EVT-0904110538-0098',
      eventType: 'checkout_dropoff',
      action: 'retry_later',
      outcome: 'pending',
      amount: 345200,
      customerId: 'CUST-0067',
    },
    {
      id: '7',
      timestamp: '2026-09-04T13:16:22.000Z',
      eventId: 'EVT-0904110538-0178',
      eventType: 'subscription_failure',
      action: 'stop',
      outcome: 'withheld',
      amount: 125000,
      customerId: 'CUST-0034',
    },
    {
      id: '8',
      timestamp: '2026-09-04T13:15:10.000Z',
      eventId: 'EVT-0904110538-0112',
      eventType: 'b2b_receivable',
      action: 'nudge',
      outcome: 'simulated',
      amount: 1875000,
      customerId: 'CUST-0234',
    },
  ];

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">Recent Activity</h2>
          <p className="text-sm text-text-muted mt-1">Latest recovery actions</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-info-100 text-info-700">
            Live
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {activities.map((activity) => (
          <div
            key={activity.id}
            className="flex items-center gap-4 p-4 rounded-lg border border-border bg-surface hover:bg-surface-muted transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="font-mono text-sm font-medium text-text-primary">
                  {activity.eventId}
                </span>
                <span className={cn(
                  'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                  getActionBadgeClass(activity.action)
                )}>
                  {activity.action.replace('_', ' ').toUpperCase()}
                </span>
                <span className={cn(
                  'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                  getOutcomeBadgeClass(activity.outcome)
                )}>
                  {activity.outcome.charAt(0).toUpperCase() + activity.outcome.slice(1)}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-text-secondary mt-1">
                <span className="flex items-center gap-1 text-text-muted">
                  <span className="font-mono text-sm">{activity.eventType.replace('_', ' ').toUpperCase()}</span>
                </span>
                <span className="font-mono text-sm font-medium text-text-primary">
                  Rs.{Number(activity.amount / 100).toLocaleString('en-IN')}
                </span>
                <span className="text-text-muted">
                  {activity.customerId}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3 text-sm text-text-muted whitespace-nowrap">
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-success-500" />
                <span>{activity.timestamp ? formatTime(activity.timestamp) : '---'}</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}