'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { formatAmountDisplay, formatDate, displayValue, formatStatus, formatAction, formatLadderStep } from '@/lib/format';
import { api } from '@/lib/api';
import type { ExceptionsResponse } from '@/lib/api';

interface ExceptionsPageProps {}

export function ExceptionsPage() {
  const [withheld, setWithheld] = useState<any[]>([]);
  const [needsHuman, setNeedsHuman] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'withheld' | 'needs_human'>('withheld');

  const fetchExceptions = async () => {
    setLoading(true);
    try {
      const data = await api.getExceptions();
      setWithheld(data.withheld_by_policy || []);
      setNeedsHuman(data.needs_a_human || []);
    } catch (error) {
      console.error('Failed to fetch exceptions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptions();
  }, []);

  const currentData = activeTab === 'withheld' ? withheld : needsHuman;
  const columns = [
    { key: 'id', header: 'ID', width: 'w-12' },
    { key: 'event_id', header: 'Event ID', width: 'w-32' },
    { key: 'event_type', header: 'Type', width: 'w-28' },
    { key: 'cause', header: 'Cause', width: 'w-32' },
    { key: 'action', header: 'Action', width: 'w-28' },
    { key: 'outcome', header: 'Outcome', width: 'w-24' },
    { key: 'amount_inr', header: 'Amount', width: 'w-28' },
    { key: 'created_at', header: 'Timestamp', width: 'w-40' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Exceptions</h1>
          <p className="text-text-secondary mt-1">Events requiring attention</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-border">
        <button
          onClick={() => setActiveTab('withheld')}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === 'withheld'
              ? 'bg-surface text-text-primary border-b-2 border-primary-600'
              : 'text-text-muted hover:text-text-primary'
          }`}
        >
          Withheld by Policy ({withheld.length})
        </button>
        <button
          onClick={() => setActiveTab('needs_human')}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === 'needs_human'
              ? 'bg-surface text-text-primary border-b-2 border-primary-600'
              : 'text-text-muted hover:text-text-primary'
          }`}
        >
          Needs Human ({needsHuman.length})
        </button>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">ID</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">Event ID</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">Cause</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">Action</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">Outcome</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">Amount</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-text-muted">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                      <span className="text-text-muted">Loading exceptions...</span>
                    </div>
                  </td>
                </tr>
              ) : currentData.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-text-muted">
                    No exceptions found
                  </td>
                </tr>
              ) : (
                currentData.map((row: any) => (
                  <tr key={row.id} className="border-b border-border hover:bg-surface-muted transition-colors">
                    <td className="px-4 py-3 font-mono text-sm text-text-primary">{row.id}</td>
                    <td className="px-4 py-3 font-mono text-sm text-text-primary">{row.event_id}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        row.event_type === 'checkout_dropoff' ? 'bg-info-100 text-info-700' :
                        row.event_type === 'subscription_failure' ? 'bg-warning-100 text-warning-700' :
                        'bg-success-100 text-success-700'
                      }`}>
                        {row.event_type?.replace('_', ' ').toUpperCase() || '---'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-text-primary">{row.cause || '---'}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        row.action === 'retry_now' ? 'bg-info-100 text-info-700' :
                        row.action === 'retry_later' ? 'bg-warning-100 text-warning-700' :
                        row.action === 'nudge' ? 'bg-info-100 text-info-700' :
                        row.action === 'escalate_to_human' ? 'bg-warning-100 text-warning-700' :
                        row.action === 'stop' ? 'bg-danger-100 text-danger-700' : ''
                      }`}>
                        {row.action?.replace('_', ' ').toUpperCase() || '---'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        row.outcome === 'recovered' ? 'bg-success-100 text-success-700' :
                        row.outcome === 'failed' ? 'bg-danger-100 text-danger-700' :
                        row.outcome === 'api_error' ? 'bg-info-100 text-info-700' :
                        row.outcome === 'simulated' ? 'bg-info-100 text-info-700' :
                        row.outcome === 'pending' ? 'bg-warning-100 text-warning-700' :
                        row.outcome === 'paused' ? 'bg-warning-100 text-warning-700' :
                        row.outcome === 'escalated' ? 'bg-warning-100 text-warning-700' :
                        row.outcome === 'withheld' ? 'bg-danger-100 text-danger-700' : 'bg-surface-muted text-text-muted'
                      }`}>
                        {row.outcome?.charAt(0).toUpperCase() + row.outcome?.slice(1) || '---'}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-sm font-medium text-text-primary">
                      {row.amount_inr ? `Rs.${(row.amount_inr / 100).toLocaleString('en-IN')}` : '---'}
                    </td>
                    <td className="px-4 py-3 text-sm text-text-secondary">
                      {row.created_at ? formatDate(row.created_at) : '---'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}