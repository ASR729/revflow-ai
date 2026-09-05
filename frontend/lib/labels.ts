/**
 * Presentational labels/tag-tone mapping for contract enum values.
 * Pure lookups; no metric arithmetic.
 */

export type Tone =
  | 'recovered'
  | 'atrisk'
  | 'stopped'
  | 'simulated'
  | 'navy'
  | 'neutral';

export const ACTION_LABEL: Record<string, string> = {
  retry_now: 'Retry now',
  retry_later: 'Retry later',
  nudge: 'Nudge',
  escalate_to_human: 'Escalate',
  stop: 'Stop',
};

export const ACTION_TONE: Record<string, Tone> = {
  retry_now: 'navy',
  retry_later: 'atrisk',
  nudge: 'navy',
  escalate_to_human: 'atrisk',
  stop: 'stopped',
};

export const OUTCOME_LABEL: Record<string, string> = {
  recovered: 'Recovered',
  failed: 'Failed',
  api_error: 'API error',
  simulated: 'Simulated',
  pending: 'Pending',
  paused: 'Paused',
  escalated: 'Escalated',
  withheld: 'Withheld',
};

export const OUTCOME_TONE: Record<string, Tone> = {
  recovered: 'recovered',
  failed: 'stopped',
  api_error: 'stopped',
  simulated: 'simulated',
  pending: 'atrisk',
  paused: 'atrisk',
  escalated: 'atrisk',
  withheld: 'stopped',
};

export const LADDER_LABEL: Record<string, string> = {
  none: 'None',
  gentle_reminder: 'Gentle reminder',
  firm_reminder: 'Firm reminder',
  flag_for_human: 'Flag for human',
};

export const LADDER_TONE: Record<string, Tone> = {
  none: 'neutral',
  gentle_reminder: 'navy',
  firm_reminder: 'atrisk',
  flag_for_human: 'stopped',
};

export const EVENT_TYPE_LABEL: Record<string, string> = {
  checkout_dropoff: 'Checkout dropoff',
  subscription_failure: 'Subscription failure',
  b2b_receivable: 'B2B receivable',
};

export const CAUSE_LABEL: Record<string, string> = {
  insufficient_funds: 'Insufficient funds',
  bank_timeout: 'Bank timeout',
  technical_decline: 'Technical decline',
  business_decline: 'Business decline',
  authentication_failed: 'Authentication failed',
  session_timeout: 'Session timeout',
  user_abandoned: 'User abandoned',
  mandate_expired: 'Mandate expired',
  user_revoked: 'User revoked',
  invoice_overdue: 'Invoice overdue',
  invoice_disputed: 'Invoice disputed',
  awaiting_po: 'Awaiting PO',
  unclassified: 'Unclassified',
};

export const RULE_LABEL: Record<string, string> = {
  hard_stop_cause_in_denylist: 'Hard stop',
  retry_ceiling_reached: 'Retry ceiling',
  ptp_pause_active: 'PTP pause',
  ptp_promise_broken_escalated: 'PTP broken',
  contact_cap_reached: 'Contact cap',
  cooldown_active: 'Cooldown',
  ladder_not_yet_due: 'Not yet due',
  ladder_step_by_age: 'Ladder step',
  deterministic_action_table: 'Deterministic',
  llm_reasoned_within_ceiling: 'LLM reasoned',
  llm_output_rejected_defaulted: 'LLM rejected',
};

export const RUN_STATUS_LABEL: Record<string, string> = {
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
};

export const RUN_STATUS_TONE: Record<string, Tone> = {
  running: 'navy',
  completed: 'recovered',
  failed: 'stopped',
};

export function labelFor(map: Record<string, string>, key: string | null | undefined): string {
  if (!key) return '—';
  return map[key] ?? key;
}
