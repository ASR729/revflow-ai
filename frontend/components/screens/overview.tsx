'use client';

import Link from 'next/link';
import { api, type ClassifierMetricsResponse, type MetricsResponse, type RunsResponse } from '@/lib/api';
import { useApiData } from '@/lib/use-api-data';
import { PageHeader } from '@/components/app-shell';
import { CardSection, StatCard, StatCardSkeleton } from '@/components/ui/stat-card';
import { PipelineBar } from '@/components/ui/pipeline-bar';
import { EmptyState, ErrorState, PageSkeleton } from '@/components/ui/states';
import { Tag } from '@/components/ui/badge';
import { RUN_STATUS_LABEL, RUN_STATUS_TONE } from '@/lib/labels';
import {
  formatCount,
  formatCoverage,
  formatINRHeadline,
  formatINRLedger,
  formatRate,
  formatTimestamp,
} from '@/lib/format';

const NO_COMPLETED_RUNS = 'no completed runs';

export function OverviewScreen() {
  const metrics = useApiData<MetricsResponse>(() => api.getMetrics());
  const classifier = useApiData<ClassifierMetricsResponse>(() => api.getClassifierMetrics());
  const runs = useApiData<RunsResponse>(() => api.listRuns());

  const metricsMissing =
    metrics.status === 'error' && /404|no completed runs/i.test(metrics.message);

  return (
    <div>
      <PageHeader
        title="Overview"
        description="What the agent processed, decided, and recovered on the latest run."
      />

      <RunStatus runs={runs} />

      {metrics.status === 'loading' ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
      ) : metrics.status === 'error' ? (
        metricsMissing || metrics.message.includes(NO_COMPLETED_RUNS) ? (
          <EmptyState
            title="No completed runs yet"
            description="Run a batch from the header to generate the first metrics set. Everything below fills from the real pipeline output."
          />
        ) : (
          <ErrorState title="Unable to load metrics." message={metrics.message} />
        )
      ) : (
        <OverviewBody metrics={metrics.data} classifier={classifier} />
      )}

      <div className="mt-4 text-xs text-muted">
        Inspect decision lineage in <Link href="/audit" className="text-navy underline underline-offset-2">Audit Trail</Link>.
      </div>
    </div>
  );
}

function RunStatus({ runs }: { runs: ReturnType<typeof useApiData<RunsResponse>> }) {
  if (runs.status === 'loading') {
    return (
      <div className="card mb-4 flex items-center gap-3 p-4" aria-busy="true" aria-label="Loading run status">
        <div className="skeleton h-3 w-3 rounded-full" />
        <div className="skeleton h-4 w-48" />
      </div>
    );
  }
  if (runs.status === 'error') {
    return (
      <div className="card mb-4 border-stopped/30 p-4" role="alert">
        <p className="text-sm font-semibold text-stopped">Backend unavailable.</p>
        <p className="mt-0.5 text-xs text-muted">{runs.message}</p>
      </div>
    );
  }
  const latest = runs.data.runs[0];
  if (!latest) {
    return (
      <div className="card mb-4 p-4">
        <p className="text-sm text-muted">No runs recorded yet.</p>
      </div>
    );
  }
  return (
    <div className="card mb-4 flex flex-wrap items-center gap-x-6 gap-y-2 p-4">
      <div className="flex items-center gap-2">
        <Tag label={RUN_STATUS_LABEL[latest.status] ?? latest.status} tone={RUN_STATUS_TONE[latest.status] ?? 'neutral'} />
        {latest.status === 'running' ? <span className="spinner" aria-hidden="true" /> : null}
      </div>
      <p className="font-mono text-xs text-ink">{latest.run_id}</p>
      <p className="text-xs text-muted">Started {formatTimestamp(latest.started_at)}</p>
      <p className="text-xs text-muted">{formatCount(latest.event_count)} events</p>
      <p className="text-xs text-muted">{formatCount(latest.llm_call_count)} LLM calls</p>
    </div>
  );
}

function OverviewBody({
  metrics,
  classifier,
}: {
  metrics: MetricsResponse;
  classifier: ReturnType<typeof useApiData<ClassifierMetricsResponse>>;
}) {
  const m = metrics;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Recovered"
          tone="recovered"
          value={m.amounts_inr.realised_recovered}
          format={formatINRHeadline}
          caption="Real Razorpay Test Mode retries"
          ariaLabel={`Recovered: ${formatINRHeadline(m.amounts_inr.realised_recovered)} rupees`}
        />
        <StatCard
          label="At risk"
          tone="atrisk"
          value={m.amounts_inr.at_risk}
          format={formatINRHeadline}
          caption={`${formatCount(m.event_count)} events in this run`}
          ariaLabel={`At risk: ${formatINRHeadline(m.amounts_inr.at_risk)} rupees`}
        />
        <StatCard
          label="Recovery rate"
          tone="navy"
          value={m.rates.recovery_rate_realised}
          format={formatRate}
          caption={`Coverage: ${formatRate(m.rates.addressable_coverage)} · ${formatCoverage(m.event_count)}`}
          ariaLabel={
            m.rates.recovery_rate_realised === null
              ? 'Recovery rate unavailable'
              : `Recovery rate: ${formatRate(m.rates.recovery_rate_realised)} with coverage ${formatRate(m.rates.addressable_coverage)}`
          }
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <CardSection title="Recovery by pipeline" subtitle="Realised recovery rate per event type">
          <div className="space-y-5">
            <PipelineBar
              label="Checkout dropoff"
              rate={m.by_pipeline.checkout_dropoff.recovery_rate_realised}
              coverage={formatCoverage(m.by_pipeline.checkout_dropoff.event_count)}
              tone="navy"
            />
            <PipelineBar
              label="Subscription failure"
              rate={m.by_pipeline.subscription_failure.recovery_rate_realised}
              coverage={formatCoverage(m.by_pipeline.subscription_failure.event_count)}
              tone="navy"
            />
            <PipelineBar
              label="B2B receivable"
              rate={m.by_pipeline.b2b_receivable.recovery_rate_realised}
              coverage={formatCoverage(m.by_pipeline.b2b_receivable.event_count)}
              tone="navy"
            />
          </div>
        </CardSection>

        <CardSection title="Boundedness" subtitle="Where the ceiling held">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div>
              <dt className="text-xs text-muted">Correctly withheld</dt>
              <dd className="font-semibold tabular-nums text-stopped">{formatCount(m.boundedness.withheld_count)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">Escalated to humans</dt>
              <dd className="font-semibold tabular-nums text-atrisk">{formatCount(m.boundedness.escalated_count)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">Decided without LLM</dt>
              <dd className="font-semibold tabular-nums text-ink">{formatRate(m.boundedness.deterministic_share)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">LLM budget used</dt>
              <dd className="font-semibold tabular-nums text-ink">
                {formatCount(m.boundedness.llm_call_count)} / {formatCount(m.boundedness.llm_call_budget)}
              </dd>
            </div>
          </dl>
        </CardSection>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <CardSection title="Integrity" subtitle="False-positive and harassment guards">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div>
              <dt className="text-xs text-muted">False positives</dt>
              <dd className="font-semibold tabular-nums text-ink">{formatCount(m.integrity.false_positive_count)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">False-positive cost</dt>
              <dd className="font-semibold tabular-nums text-ink">{formatINRLedger(m.integrity.false_positive_cost_inr)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">Harassment incidents</dt>
              <dd className="font-semibold tabular-nums text-ink">{formatCount(m.integrity.harassment_incident_count)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">Over-retry incidents</dt>
              <dd className="font-semibold tabular-nums text-ink">{formatCount(m.integrity.over_retry_count)}</dd>
            </div>
          </dl>
        </CardSection>

        <CardSection title="Action breakdown" subtitle="Decisions taken this run">
          <ul className="space-y-2 text-sm">
            {(
              [
                ['Retry now', m.action_breakdown.retry_now],
                ['Retry later', m.action_breakdown.retry_later],
                ['Nudge (simulated)', m.action_breakdown.nudge],
                ['Escalate to human', m.action_breakdown.escalate_to_human],
                ['Stop (withheld)', m.action_breakdown.stop],
              ] as const
            ).map(([label, count]) => (
              <li key={label} className="flex items-center justify-between border-b border-edge pb-2 last:border-b-0 last:pb-0">
                <span className="text-ink">{label}</span>
                <span className="font-semibold tabular-nums text-ink">{formatCount(count)}</span>
              </li>
            ))}
          </ul>
        </CardSection>
      </div>

      <CardSection title="Classifier" subtitle="Classifier quality for this run">
        {classifier.status === 'loading' ? (
          <div className="space-y-2" aria-busy="true">
            <div className="skeleton h-4 w-2/3" />
            <div className="skeleton h-4 w-1/2" />
          </div>
        ) : classifier.status === 'error' ? (
          <p className="text-sm text-muted">Classifier metrics unavailable for this run.</p>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
            <PipelineBar
              label="Accuracy"
              rate={classifier.data.overall.accuracy}
              coverage={formatCoverage(classifier.data.overall.support)}
              tone="recovered"
            />
            <PipelineBar
              label="Macro precision"
              rate={classifier.data.overall.macro_precision}
              coverage={formatCoverage(classifier.data.overall.support)}
              tone="recovered"
            />
            <PipelineBar
              label="Macro recall"
              rate={classifier.data.overall.macro_recall}
              coverage={formatCoverage(classifier.data.overall.support)}
              tone="recovered"
            />
          </div>
        )}
      </CardSection>

      <p className="text-xs text-muted">
        Run <span className="font-mono">{m.run_id}</span> · generated {formatTimestamp(m.generated_at)} · seed{' '}
        <span className="font-mono">{m.random_seed}</span> · LLM mode {m.llm_mode}
      </p>
    </div>
  );
}

export { PageSkeleton as OverviewSkeleton };
