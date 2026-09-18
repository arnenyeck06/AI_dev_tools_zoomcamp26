// Small date helpers. Everything else in the app deals with plain
// yyyy-mm-dd / yyyy-mm strings so it stays JSON-serializable the same
// way it will once a real backend is behind `api/client.ts`.

export function todayISO(): string {
  return toISODate(new Date());
}

export function toISODate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function monthKeyOf(dateISO: string): string {
  return dateISO.slice(0, 7);
}

export function currentMonthKey(): string {
  return monthKeyOf(todayISO());
}

export function addMonths(monthKey: string, delta: number): string {
  const [y, m] = monthKey.split('-').map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

export function daysInMonth(monthKey: string): number {
  const [y, m] = monthKey.split('-').map(Number);
  return new Date(y, m, 0).getDate();
}

/** Build a yyyy-mm-dd within `monthKey`, clamping the day to that month's length. */
export function dateInMonth(monthKey: string, day: number): string {
  const clamped = Math.min(Math.max(day, 1), daysInMonth(monthKey));
  return `${monthKey}-${String(clamped).padStart(2, '0')}`;
}

const MONTH_LABELS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export function formatMonthLabel(monthKey: string): string {
  const [y, m] = monthKey.split('-').map(Number);
  return `${MONTH_LABELS[m - 1]} ${y}`;
}

export function formatMonthShort(monthKey: string): string {
  const [, m] = monthKey.split('-').map(Number);
  return MONTH_LABELS[m - 1].slice(0, 3);
}

export function formatDateLabel(dateISO: string): string {
  const [y, m, d] = dateISO.split('-').map(Number);
  return `${MONTH_LABELS[m - 1].slice(0, 3)} ${d}, ${y}`;
}

export function formatCurrency(amount: number): string {
  return amount.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
