import { addMonths, formatMonthLabel } from '../lib/date';

export default function MonthSwitcher({
  month,
  onChange,
}: {
  month: string;
  onChange: (month: string) => void;
}) {
  return (
    <div className="month-switcher">
      <button aria-label="Previous month" onClick={() => onChange(addMonths(month, -1))}>
        ‹
      </button>
      <span className="month-label">{formatMonthLabel(month)}</span>
      <button aria-label="Next month" onClick={() => onChange(addMonths(month, 1))}>
        ›
      </button>
    </div>
  );
}
