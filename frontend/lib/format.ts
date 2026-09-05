/**
 * RevFlow formatting utilities.
 *
 * Intl.NumberFormat('en-IN') lives ONLY in this file.
 * Components receive ready-to-render strings; no metric arithmetic here or there.
 * Timestamps arrive as UTC and render in Asia/Kolkata per contract 10.2.
 */

const inrNoDecimals = new Intl.NumberFormat('en-IN', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const inrTwoDecimals = new Intl.NumberFormat('en-IN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const ratioPercent = new Intl.NumberFormat('en-IN', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const istDate = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
});

const isUsable = (v: number | null | undefined): v is number =>
  typeof v === 'number' && !Number.isNaN(v);

/** Headline currency, rupees, no decimals: ₹2,84,600 */
export function formatINRHeadline(rupees: number | null | undefined): string {
  if (!isUsable(rupees)) return '—';
  return `₹${inrNoDecimals.format(rupees)}`;
}

/** Ledger currency, rupees, two decimals: ₹1,200.00 */
export function formatINRLedger(rupees: number | null | undefined): string {
  if (!isUsable(rupees)) return '—';
  return `₹${inrTwoDecimals.format(rupees)}`;
}

/** Rate 0..1 -> "72.4%"; null -> "—" */
export function formatRate(rate: number | null | undefined): string {
  if (!isUsable(rate)) return '—';
  return ratioPercent.format(rate);
}

/** Integer count with Indian grouping: 1,00,000 */
export function formatCount(value: number | null | undefined): string {
  if (!isUsable(value)) return '—';
  return inrNoDecimals.format(value);
}

/** Millisecond latency display: 243 ms */
export function formatLatency(ms: number | null | undefined): string {
  if (!isUsable(ms)) return '—';
  return `${inrNoDecimals.format(ms)} ms`;
}

/** UTC ISO timestamp -> "23 Aug 2026, 14:05" in Asia/Kolkata */
export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return istDate.format(d);
}

/** Coverage caption beside a rate: "3,00,000 events" style fragments are NOT
 *  computed here; callers pass the API count, this only formats it. */
export function formatCoverage(count: number | null | undefined): string {
  if (!isUsable(count)) return 'Coverage unavailable';
  return `${inrNoDecimals.format(count)} events`;
}

/** Bar fill width for a 0..1 rate — visual formatting only; components do no arithmetic. */
export function formatBarWidth(rate: number): string {
  return ratioPercent.format(rate);
}

export function displayOrDash(value: string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—';
  return value;
}
