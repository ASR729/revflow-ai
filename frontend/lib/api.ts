/**
 * RevFlow Typed API Client
 * 
 * Single source of truth for all API interactions.
 * All frontend components MUST use this client for API calls.
 * No direct fetch() calls in components.
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  EventType,
  Cause,
  Action,
  LadderStep,
  Outcome,
  RuleFired,
  CauseSource,
  SimulatedChannel,
  Locale,
  PTPStatus,
  BatchRunStatus,
} from '@/lib/contracts';

// ============================================
// Types
// ============================================

interface APIResponse<T> {
  data: T;
  status: number;
}

interface HealthResponse {
  status: string;
  version: string;
  db: string;
  razorpay_mode: string;
}

interface RunBatchRequest {
  use_llm: boolean;
  regenerate_dataset: boolean;
}

interface RunBatchResponse {
  run_id: string;
  status: 'running';
  poll: string;
}

interface BatchRunRow {
  run_id: string;
  started_at: string;
  completed_at: string | null;
  status: 'running' | 'completed' | 'failed';
  event_count: number;
  llm_call_count: number;
  random_seed: number;
  notes: string | null;
}

interface RunsResponse {
  runs: BatchRunRow[];
}

interface EventRow {
  event_id: string;
  run_id: string;
  event_type: EventType;
  amount_inr: number;
  currency: string;
  customer_id: string;
  decline_code: string | null;
  decline_message: string | null;
  retry_count: number;
  last_attempt_at: string | null;
  paused_until: string | null;
  ladder_step: LadderStep;
  invoice_issued_at: string | null;
  invoice_due_date: string | null;
  session_started_at: string | null;
  checkout_resume_token: string | null;
  customer_reply_text: string | null;
  created_at: string;
}

interface EventsResponse {
  events: EventRow[];
  total: number;
}

interface AmountsINR {
  at_risk: number;
  addressable: number;
  realised_recovered: number;
  simulated_outreach: number;
  deferred: number;
  withheld: number;
  escalated: number;
}

interface Rates {
  recovery_rate_realised: number | null;
  addressable_coverage: number;
  retry_success_rate: number | null;
}

interface PipelineMetrics {
  event_count: number;
  at_risk_inr: number;
  addressable_inr: number;
  realised_recovered_inr: number;
  recovery_rate_realised: number | null;
}

interface ByPipeline {
  checkout_dropoff: PipelineMetrics;
  subscription_failure: PipelineMetrics;
  b2b_receivable: PipelineMetrics;
}

interface Boundedness {
  withheld_count: number;
  escalated_count: number;
  deterministic_share: number;
  llm_call_count: number;
  llm_call_budget: number;
  out_of_bounds_action_count: number;
  missing_rationale_count: number;
  p95_decision_latency_ms: number;
}

interface Integrity {
  false_positive_count: number;
  false_positive_cost_inr: number;
  harassment_incident_count: number;
  over_retry_count: number;
}

interface ActionBreakdown {
  retry_now: number;
  retry_later: number;
  nudge: number;
  escalate_to_human: number;
  stop: number;
}

interface OutcomeBreakdown {
  recovered: number;
  failed: number;
  api_error: number;
  simulated: number;
  pending: number;
  paused: number;
  escalated: number;
  withheld: number;
}

interface MetricsResponse {
  run_id: string;
  generated_at: string;
  random_seed: number;
  llm_mode: 'live' | 'cached' | 'disabled';
  event_count: number;
  amounts_inr: AmountsINR;
  rates: Rates;
  by_pipeline: ByPipeline;
  boundedness: Boundedness;
  integrity: Integrity;
  action_breakdown: ActionBreakdown;
  outcome_breakdown: OutcomeBreakdown;
}

interface ClassifierMetricsResponse {
  run_id: string;
  generated_at: string;
  overall: {
    accuracy: number;
    macro_precision: number;
    macro_recall: number;
    support: number;
  };
  by_cause: Record<string, {
    precision: number;
    recall: number;
    f1: number;
    support: number;
  }>;
  by_source: {
    rule: { count: number; accuracy: number };
    llm: { count: number; accuracy: number };
  };
  confusion_pairs: Array<{
    predicted_cause: string;
    count: number;
  }>;
}

interface AuditLogRow {
  id: number;
  run_id: string;
  event_id: string;
  event_type: string;
  cause: string;
  cause_source: string;
  rule_fired: string;
  action: string;
  ladder_step: string;
  rationale: string;
  outcome: string;
  amount_inr: number;
  attributed_recovery_inr: number;
  is_simulated: number;
  llm_calls_used: number;
  latency_ms: number;
  created_at: string;
  customer_id: string;
  decline_code: string | null;
  simulated_channel: string | null;
}

interface AuditLogQuery {
  run_id?: string;
  event_type?: string;
  cause?: string;
  action?: string;
  sort?: 'timestamp' | 'amount' | 'cause';
  order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

interface AuditLogResponse {
  run_id: string;
  total: number;
  limit: number;
  offset: number;
  rows: AuditLogRow[];
}

interface ExceptionRow extends AuditLogRow {}

interface ExceptionsResponse {
  run_id: string;
  withheld_by_policy: ExceptionRow[];
  needs_a_human: ExceptionRow[];
}

interface EventDetailResponse {
  event: EventRow;
  timeline: AuditLogRow[];
  simulated_actions: SimulatedActionRow[];
  escalations: EscalationRow[];
  ptp_commitments: PTPCommitmentRow[];
}

interface SimulatedActionRow {
  id: number;
  audit_log_id: number;
  channel: SimulatedChannel;
  locale: string;
  body_text: string;
  tts_audio_path: string | null;
  status: string;
  created_at: string;
}

interface EscalationRow {
  id: number;
  audit_log_id: number;
  reason: string;
  ladder_step: string;
  queue: string;
  created_at: string;
}

interface PTPCommitmentRow {
  id: number;
  run_id: string;
  event_id: string;
  promised_date: string;
  detected_from_text: string;
  detection_source: 'rule' | 'llm';
  status: 'active' | 'kept' | 'broken';
  ladder_step_at_pause: string;
  created_at: string;
}

interface WebhookRequest {
  event: string;
  payload: Record<string, unknown>;
}

interface WebhookResponse {
  event_id: string;
  run_id: string;
  accepted: boolean;
}

interface ConfigResponse {
  MAX_RETRIES: number;
  COOLDOWN_HOURS: number;
  RETRY_BACKOFF_HOURS: number[];
  CHECKOUT_SESSION_WINDOW_MINUTES: number;
  MAX_CONTACTS_PER_CUSTOMER_PER_DAY: number;
  STOP_IF_CAUSE_IN: string[];
  LADDER_GENTLE_AFTER_DAYS: number;
  LADDER_FIRM_AFTER_DAYS: number;
  LADDER_FLAG_AFTER_DAYS: number;
  PTP_GRACE_DAYS: number;
  LLM_CALL_BUDGET_PER_RUN: number;
  LLM_MAX_ATTEMPTS: number;
  LLM_TIMEOUT_SECONDS: number;
  BATCH_SIZE: number;
  RANDOM_SEED: number;
  DECISION_LATENCY_BUDGET_MS: number;
  editable: boolean;
  note: string;
}

// ============================================
// API Client
// ============================================

class APIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = '') {
    // In browser, use backend URL directly (CORS configured on backend for localhost:3000)
    // During SSR, use backend URL directly
    const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
    this.baseURL = baseURL || (configured && configured.length > 0 ? configured : '/api');
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<{ detail?: string }>) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred';
        return Promise.reject(new Error(message));
      }
    );
  }

  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  async listRuns(): Promise<RunsResponse> {
    const response = await this.client.get<RunsResponse>('/runs');
    return response.data;
  }

  async runBatch(request: RunBatchRequest): Promise<RunBatchResponse> {
    const response = await this.client.post<RunBatchResponse>('/run-batch', request);
    return response.data;
  }

  async getMetrics(runId?: string): Promise<MetricsResponse> {
    const url = runId ? `/metrics?run_id=${runId}` : '/metrics';
    const response = await this.client.get<MetricsResponse>(url);
    return response.data;
  }

  async getClassifierMetrics(runId?: string): Promise<ClassifierMetricsResponse> {
    const url = runId ? `/classifier-metrics?run_id=${runId}` : '/classifier-metrics';
    const response = await this.client.get<ClassifierMetricsResponse>(url);
    return response.data;
  }

  async getAuditLog(query: AuditLogQuery = {}): Promise<AuditLogResponse> {
    const params = new URLSearchParams();
    if (query.run_id) params.append('run_id', query.run_id);
    if (query.event_type) params.append('event_type', query.event_type);
    if (query.cause) params.append('cause', query.cause);
    if (query.action) params.append('action', query.action);
    if (query.sort) params.append('sort', query.sort);
    if (query.order) params.append('order', query.order);
    if (query.limit) params.append('limit', String(query.limit));
    if (query.offset) params.append('offset', String(query.offset));

    const response = await this.client.get<AuditLogResponse>(`/audit-log?${params.toString()}`);
    return response.data;
  }

  async getExceptions(runId?: string): Promise<ExceptionsResponse> {
    const url = runId ? `/exceptions?run_id=${runId}` : '/exceptions';
    const response = await this.client.get<ExceptionsResponse>(url);
    return response.data;
  }

  async getEventDetail(eventId: string): Promise<EventDetailResponse> {
    const response = await this.client.get<EventDetailResponse>(`/events/${eventId}`);
    return response.data;
  }

  async getConfig(): Promise<ConfigResponse> {
    const response = await this.client.get<ConfigResponse>('/config');
    return response.data;
  }

  async postWebhook(payload: WebhookRequest): Promise<WebhookResponse> {
    const response = await this.client.post<WebhookResponse>('/webhook', payload);
    return response.data;
  }
}

// Singleton instance
export const api = new APIClient();

// Export types and client
export type {
  APIResponse,
  HealthResponse,
  RunBatchRequest,
  RunBatchResponse,
  RunsResponse,
  BatchRunRow,
  EventRow,
  EventsResponse,
  AmountsINR,
  Rates,
  PipelineMetrics,
  ByPipeline,
  Boundedness,
  Integrity,
  ActionBreakdown,
  OutcomeBreakdown,
  MetricsResponse,
  ClassifierMetricsResponse,
  AuditLogRow,
  AuditLogQuery,
  AuditLogResponse,
  ExceptionRow,
  ExceptionsResponse,
  EventDetailResponse,
  SimulatedActionRow,
  EscalationRow,
  PTPCommitmentRow,
  WebhookRequest,
  WebhookResponse,
  ConfigResponse,
};