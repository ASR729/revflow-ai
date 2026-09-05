'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { formatDate, formatAmountDisplay, displayValue, formatStatus, formatAction, formatLadderStep } from '@/lib/format';
import { Search, Filter, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '@/lib/api';
import type { AuditLogResponse, AuditLogQuery } from '@/lib/api';

interface AuditPageProps {}

export function AuditPage() {
  const [auditData, setAuditData] = useState<{ rows: any[]; total: number }>({ rows: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState<AuditLogQuery>({
    run_id: '',
    event_type: '',
    cause: '',
    action: '',
    sort: 'timestamp',
    order: 'desc',
    limit: 100,
    offset: 0,
  });
  const [filters, setFilters] = useState({
    event_type: '',
    cause: '',
    action: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 50,
    total: 0,
  });

  const fetchAuditLog = async () => {
    setLoading(true);
    try {
      const auditQuery: AuditLogQuery = {
        run_id: query.run_id || undefined,
        event_type: filters.event_type || undefined,
        cause: filters.cause || undefined,
        action: filters.action || undefined,
        sort: query.sort,
        order: query.order,
        limit: query.limit,
        offset: query.offset,
      };
      const data = await api.getAuditLog(auditQuery);
      setAuditData({ rows: data.rows, total: data.total });
    } catch (error) {
      console.error('Failed to fetch audit log:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLog();
  }, [query, filters, pagination.page]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setQuery(prev => ({ ...prev, offset: 0 }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setPagination(prev => ({ ...prev, page }));
    setQuery(prev => ({ ...prev, offset: (page - 1) * (query.limit ?? 100) }));
  };

  const handleSort = (sort: 'timestamp' | 'amount' | 'cause') => {
    setQuery(prev => ({
      ...prev,
      sort: prev.sort === sort && prev.order === 'desc' ? sort : sort,
      order: prev.sort === sort && prev.order === 'desc' ? 'asc' : 'desc',
      offset: 0,
    }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleExport = async () => {
    // Export functionality
  };

  const getEventTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      checkout_dropoff: 'bg-info-100 text-info-700',
      subscription_failure: 'bg-warning-100 text-warning-700',
      b2b_receivable: 'bg-success-100 text-success-700',
    };
    return colors[type] || 'bg-surface-muted text-text-muted';
  };

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
          <h1 className="text-2xl font-bold text-text-primary">Audit Trail</h1>
          <p className="text-text-secondary mt-1">Complete audit trail of all recovery actions</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            className="btn-secondary"
            onClick={handleExport}
            disabled={loading}
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-text-secondary mb-1">Run ID</label>
            <input
              type="text"
              value={query.run_id}
              onChange={(e) => setQuery(prev => ({ ...prev, run_id: e.target.value, offset: 0 }))}
              placeholder="Run ID"
              className="input"
            />
          </div>
          <div className="w-48">
            <label className="block text-sm font-medium text-text-secondary mb-1">Event Type</label>
            <select
              value={filters.event_type}
              onChange={(e) => handleFilterChange('event_type', e.target.value)}
              className="input"
            >
              <option value="">All Types</option>
              <option value="checkout_dropoff">Checkout Dropoff</option>
              <option value="subscription_failure">Subscription Failure</option>
              <option value="b2b_receivable">B2B Receivable</option>
            </select>
          </div>
          <div className="w-48">
            <label className="block text-sm font-medium text-text-secondary mb-1">Cause</label>
            <select
              value={filters.cause}
              onChange={(e) => handleFilterChange('cause', e.target.value)}
              className="input"
            >
              <option value="">All Causes</option>
              <option value="insufficient_funds">Insufficient Funds</option>
              <option value="bank_timeout">Bank Timeout</option>
              <option value="technical_decline">Technical Decline</option>
              <option value="business_decline">Business Decline</option>
              <option value="authentication_failed">Authentication Failed</option>
              <option value="session_timeout">Session Timeout</option>
              <option value="user_abandoned">User Abandoned</option>
              <option value="mandate_expired">Mandate Expired</option>
              <option value="user_revoked">User Revoked</option>
              <option value="invoice_overdue">Invoice Overdue</option>
              <option value="invoice_disputed">Invoice Disputed</option>
              <option value="awaiting_po">Awaiting PO</option>
              <option value="unclassified">Unclassified</option>
            </select>
          </div>
          <div className="w-40">
            <label className="block text-sm font-medium text-text-secondary mb-1">Action</label>
            <select
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
              className="input"
            >
              <option value="">All Actions</option>
              <option value="retry_now">Retry Now</option>
              <option value="retry_later">Retry Later</option>
              <option value="nudge">Nudge</option>
              <option value="escalate_to_human">Escalate to Human</option>
              <option value="stop">Stop</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
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
                      <span className="text-text-muted">Loading audit log...</span>
                    </div>
                  </td>
                </tr>
              ) : auditData.rows.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-text-muted">
                    No audit records found
                  </td>
                </tr>
              ) : (
                auditData.rows.map((row: any) => (
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

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-4 border-t border-border">
          <div className="text-sm text-text-muted">
            Showing {((pagination.page - 1) * pagination.pageSize) + 1} to{' '}
            {Math.min(pagination.page * pagination.pageSize, auditData.total)} of{' '}
            {auditData.total} results
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page === 1 || loading}
              className="btn-secondary btn-sm"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 text-sm text-text-secondary">
              Page {pagination.page} of {Math.ceil(auditData.total / pagination.pageSize)}
            </span>
            <button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= Math.ceil(auditData.total / pagination.pageSize) || loading}
              className="btn-secondary btn-sm"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}