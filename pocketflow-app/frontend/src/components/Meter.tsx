export type MeterStatus = 'good' | 'warning' | 'critical';

export function meterStatus(value: number, max: number): MeterStatus {
  const ratio = max > 0 ? value / max : 0;
  if (ratio < 0.7) return 'good';
  if (ratio < 1) return 'warning';
  return 'critical';
}

/** A single ratio against a limit — used for budget-vs-actual per category. */
export default function Meter({ value, max }: { value: number; max: number }) {
  const ratio = max > 0 ? value / max : 0;
  const pct = Math.min(Math.max(ratio, 0), 1) * 100;
  const status = meterStatus(value, max);
  return (
    <div
      className="meter-track"
      role="img"
      aria-label={`${Math.round(ratio * 100)}% of budget used`}
    >
      <div className={`meter-fill meter-fill--${status}`} style={{ width: `${pct}%` }} />
    </div>
  );
}
