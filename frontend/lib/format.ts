/**
 * RevFlow Formatting Utilities
 * 
 * Centralized formatting functions for the frontend.
 * All number formatting MUST use these utilities.
 * No component should create its own Intl.NumberFormat instances.
 */

// Indian number formatting (lakh/crore)
const indianFormatter = new Intl.NumberFormat('en-IN', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const indianCurrencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const indianDecimalFormatter = new Intl.NumberFormat('en-IN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const percentageFormatter = new Intl.NumberFormat('en-IN', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const decimalFormatter = new Intl.NumberFormat('en-IN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Format a number in Indian numbering system (lakh/crore)
 * e.g., 100000 -> "1,00,000", 10000000 -> "1,00,00,000"
 */
export function formatINR(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '—';
  }
  return indianFormatter.format(amount);
}

/**
 * Format amount as Indian currency (₹)
 */
export function formatINRCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '—';
  }
  return indianCurrencyFormatter.format(amount);
}

/**
 * Format amount in paise as INR currency
 * Backend stores amounts in paise, so divide by 100
 */
export function formatPaiseAsINR(paise: number | null | undefined): string {
  if (paise === null || paise === undefined || isNaN(paise)) {
    return '—';
  }
  return indianCurrencyFormatter.format(paise / 100);
}

/**
 * Format a decimal number with 2 decimal places
 */
export function formatDecimal(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '—';
  }
  return indianDecimalFormatter.format(value);
}

/**
 * Format a percentage value (0-1 -> 0%-100%)
 */
export function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '—';
  }
  return percentageFormatter.format(value);
}

/**
 * Format a rate as percentage (0-1 -> 0.0%-100.0%)
 */
export function formatRate(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '—';
  }
  return percentageFormatter.format(value);
}

/**
 * Format a count with Indian grouping
 */
export function formatCount(count: number | null | undefined): string {
  if (count === null || count === undefined || isNaN(count)) {
    return '—';
  }
  return indianFormatter.format(count);
}

/**
 * Format a date for display
 * Uses manual UTC formatting to ensure consistent server/client rendering
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '—';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '—';
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const day = date.getUTCDate();
    const month = months[date.getUTCMonth()];
    const year = date.getUTCFullYear();
    const hours = date.getUTCHours();
    const minutes = date.getUTCMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    return `${day} ${month} ${year}, ${displayHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')} ${ampm}`;
  } catch {
    return '—';
  }
}

/**
 * Format a time for display (time only)
 * Uses manual UTC formatting to ensure consistent server/client rendering
 */
export function formatTime(dateString: string | null | undefined): string {
  if (!dateString) return '—';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '—';
    const hours = date.getUTCHours();
    const minutes = date.getUTCMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    return `${displayHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')} ${ampm}`;
  } catch {
    return '—';
  }
}

/**
 * Format a date for short display (date only)
 * Uses manual UTC formatting to ensure consistent server/client rendering
 */
export function formatDateShort(dateString: string | null | undefined): string {
  if (!dateString) return '—';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '—';
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const day = date.getUTCDate();
    const month = months[date.getUTCMonth()];
    const year = date.getUTCFullYear();
    return `${day} ${month} ${year}`;
  } catch {
    return '—';
  }
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return '—';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '—';
    
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return formatDateShort(dateString);
  } catch {
    return '—';
  }
}

/**
 * Format amount in paise as INR with lakh/crore formatting
 * For display in tables/cards
 */
export function formatAmountDisplay(paise: number | null | undefined): string {
  if (paise === null || paise === undefined || isNaN(paise)) {
    return '—';
  }
  const rupees = paise / 100;
  if (rupees >= 10000000) {
    return `₹${(rupees / 10000000).toFixed(2)} Cr`;
  } else if (rupees >= 100000) {
    return `₹${(rupees / 100000).toFixed(2)} L`;
  } else if (rupees >= 1000) {
    return `₹${(rupees / 1000).toFixed(1)}K`;
  }
  return `₹${rupees.toLocaleString('en-IN')}`;
}

/**
 * Format a status for display
 */
export function formatStatus(status: string): { label: string; className: string } {
  const statusMap: Record<string, { label: string; className: string }> = {
    running: { label: 'Running', className: 'status-running' },
    completed: { label: 'Completed', className: 'status-completed' },
    failed: { label: 'Failed', className: 'status-failed' },
    pending: { label: 'Pending', className: 'status-pending' },
    paused: { label: 'Paused', className: 'status-paused' },
    recovered: { label: 'Recovered', className: 'status-recovered' },
    api_error: { label: 'API Error', className: 'status-api-error' },
    simulated: { label: 'Simulated', className: 'status-simulated' },
    escalated: { label: 'Escalated', className: 'status-escalated' },
    withheld: { label: 'Withheld', className: 'status-withheld' },
  };
  
  return statusMap[status] || { label: status, className: '' };
}

/**
 * Format action for display
 */
export function formatAction(action: string): { label: string; className: string } {
  const actionMap: Record<string, { label: string; className: string }> = {
    retry_now: { label: 'Retry Now', className: 'action-retry_now' },
    retry_later: { label: 'Retry Later', className: 'action-retry_later' },
    nudge: { label: 'Nudge', className: 'action-nudge' },
    escalate_to_human: { label: 'Escalate', className: 'action-escalate_to_human' },
    stop: { label: 'Stop', className: 'action-stop' },
  };
  
  return actionMap[action] || { label: action, className: '' };
}

/**
 * Format ladder step for display
 */
export function formatLadderStep(step: string): { label: string; className: string } {
  const stepMap: Record<string, { label: string; className: string }> = {
    none: { label: 'None', className: 'ladder-none' },
    gentle_reminder: { label: 'Gentle Reminder', className: 'ladder-gentle_reminder' },
    firm_reminder: { label: 'Firm Reminder', className: 'ladder-firm_reminder' },
    flag_for_human: { label: 'Flag for Human', className: 'ladder-flag_for_human' },
  };
  
  return stepMap[step] || { label: step, className: '' };
}

/**
 * Format rule fired for display
 */
export function formatRuleFired(rule: string): { label: string; className: string } {
  const ruleMap: Record<string, { label: string; className: string }> = {
    hard_stop_cause_in_denylist: { label: 'Hard Stop', className: 'rule-hard_stop' },
    retry_ceiling_reached: { label: 'Retry Ceiling', className: 'rule-retry_ceiling' },
    ptp_pause_active: { label: 'PTP Pause', className: 'rule-ptp_pause' },
    ptp_promise_broken_escalated: { label: 'PTP Broken', className: 'rule-ptp_broken' },
    contact_cap_reached: { label: 'Contact Cap', className: 'rule-contact_cap' },
    cooldown_active: { label: 'Cooldown', className: 'rule-cooldown' },
    ladder_not_yet_due: { label: 'Not Yet Due', className: 'rule-ladder_not_due' },
    ladder_step_by_age: { label: 'Ladder Step', className: 'rule-ladder_step' },
    deterministic_action_table: { label: 'Deterministic', className: 'rule-deterministic' },
    llm_reasoned_within_ceiling: { label: 'LLM Reasoned', className: 'rule-llm_reasoned' },
    llm_output_rejected_defaulted: { label: 'LLM Rejected', className: 'rule-llm_rejected' },
  };
  
  return ruleMap[rule] || { label: rule, className: '' };
}

/**
 * Null-safe value display
 * Returns '—' for null/undefined/NaN
 */
export function displayValue<T>(value: T | null | undefined, formatter?: (v: T) => string): string {
  if (value === null || value === undefined || (typeof value === 'number' && isNaN(value))) {
    return '—';
  }
  return formatter ? formatter(value) : String(value);
}