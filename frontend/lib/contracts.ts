/**
 * RevFlow Frontend Contracts
 * 
 * Mirrors backend/revflow/contracts/enums.py exactly.
 * This file MUST stay in sync with backend/revflow/contracts/enums.py
 * TEST-12 asserts parity between this file and the backend enums.
 * 
 * Do NOT modify enum values without updating the backend enums.py and vice versa.
 */

export type EventType = 
  | 'checkout_dropoff'
  | 'subscription_failure'
  | 'b2b_receivable';

export type Cause = 
  | 'insufficient_funds'
  | 'bank_timeout'
  | 'technical_decline'
  | 'business_decline'
  | 'authentication_failed'
  | 'session_timeout'
  | 'user_abandoned'
  | 'mandate_expired'
  | 'user_revoked'
  | 'invoice_overdue'
  | 'invoice_disputed'
  | 'awaiting_po'
  | 'unclassified';

export type Action = 
  | 'retry_now'
  | 'retry_later'
  | 'nudge'
  | 'escalate_to_human'
  | 'stop';

export type LadderStep = 
  | 'none'
  | 'gentle_reminder'
  | 'firm_reminder'
  | 'flag_for_human';

export type Outcome = 
  | 'recovered'
  | 'failed'
  | 'api_error'
  | 'simulated'
  | 'pending'
  | 'paused'
  | 'escalated'
  | 'withheld';

export type RuleFired = 
  | 'hard_stop_cause_in_denylist'
  | 'retry_ceiling_reached'
  | 'ptp_pause_active'
  | 'ptp_promise_broken_escalated'
  | 'contact_cap_reached'
  | 'cooldown_active'
  | 'ladder_not_yet_due'
  | 'ladder_step_by_age'
  | 'deterministic_action_table'
  | 'llm_reasoned_within_ceiling'
  | 'llm_output_rejected_defaulted';

export type CauseSource = 
  | 'rule'
  | 'llm';

export type SimulatedChannel = 
  | 'sms'
  | 'whatsapp'
  | 'voice_script';

export type Locale = 
  | 'en'
  | 'hi'
  | 'hinglish';

export type PTPStatus = 
  | 'active'
  | 'kept'
  | 'broken';

export type BatchRunStatus = 
  | 'running'
  | 'completed'
  | 'failed';

// Configuration constants (from backend contracts/config.py)
export const CONFIG = {
  MAX_RETRIES: 3,
  COOLDOWN_HOURS: 24,
  RETRY_BACKOFF_HOURS: [24, 48, 96],
  CHECKOUT_SESSION_WINDOW_MINUTES: 15,
  MAX_CONTACTS_PER_CUSTOMER_PER_DAY: 1,
  STOP_IF_CAUSE_IN: ['user_revoked', 'invoice_disputed'] as const,
  LADDER_GENTLE_AFTER_DAYS: 7,
  LADDER_FIRM_AFTER_DAYS: 21,
  LADDER_FLAG_AFTER_DAYS: 45,
  PTP_GRACE_DAYS: 2,
  LLM_CALL_BUDGET_PER_RUN: 90,
  LLM_MAX_ATTEMPTS: 3,
  LLM_TIMEOUT_SECONDS: 20,
  BATCH_SIZE: 300,
  RANDOM_SEED: 42,
  DATABASE_PATH: 'backend/data/revflow.db',
  DECISION_LATENCY_BUDGET_MS: 5000,
} as const;

// Applicability matrix (which causes apply to which event types)
export const CAUSE_APPLICABILITY: Record<string, string[]> = {
  insufficient_funds: ['checkout_dropoff', 'subscription_failure'],
  bank_timeout: ['checkout_dropoff', 'subscription_failure'],
  technical_decline: ['checkout_dropoff', 'subscription_failure'],
  business_decline: ['checkout_dropoff'],
  authentication_failed: ['checkout_dropoff'],
  session_timeout: ['checkout_dropoff'],
  user_abandoned: ['checkout_dropoff'],
  mandate_expired: ['subscription_failure'],
  user_revoked: ['subscription_failure'],
  invoice_overdue: ['b2b_receivable'],
  invoice_disputed: ['b2b_receivable'],
  awaiting_po: ['b2b_receivable'],
  unclassified: ['checkout_dropoff', 'subscription_failure', 'b2b_receivable'],
} as const;

// Hard stop causes
export const STOP_IF_CAUSE_IN = ['user_revoked', 'invoice_disputed'] as const;

// Valid action/outcome pairings
export const VALID_ACTION_OUTCOME: Record<string, string[]> = {
  retry_now: ['recovered', 'failed', 'api_error'],
  retry_later: ['pending', 'paused'],
  nudge: ['simulated'],
  escalate_to_human: ['escalated'],
  stop: ['withheld'],
} as const;

// Valid ladder_step/action pairings
export const VALID_LADDER_ACTION: Record<string, string[]> = {
  none: ['retry_now', 'retry_later', 'nudge', 'escalate_to_human', 'stop'],
  gentle_reminder: ['nudge', 'escalate_to_human'],
  firm_reminder: ['nudge', 'escalate_to_human'],
  flag_for_human: ['escalate_to_human'],
} as const;