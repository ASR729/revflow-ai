'use client';

import { PipelineVisualization } from './pipeline-visualization';
import { RecentActivity } from './recent-activity';
import { MetricsGrid } from './dashboard/metrics-grid';
import { PipelineSummary } from './pipeline-summary';

export function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Overview</h1>
          <p className="text-text-secondary mt-1">
            Real-time view of your revenue recovery pipeline
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 text-xs font-medium rounded-full bg-success-100 text-success-700">
            Live
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <MetricsGrid />

      {/* Pipeline Visualization */}
      <PipelineVisualization />

      {/* Pipeline Summary & Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <PipelineSummary />
        </div>
        <div>
          <RecentActivity />
        </div>
      </div>
    </div>
  );
}