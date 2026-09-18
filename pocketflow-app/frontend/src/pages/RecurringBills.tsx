import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import { MEMBERS } from '../api/constants';
import CategoryTag from '../components/CategoryTag';
import MonthSwitcher from '../components/MonthSwitcher';
import { currentMonthKey, formatCurrency, formatDateLabel } from '../lib/date';
import type { RecurringSuggestion } from '../api/types';

export default function RecurringBills({
  onCountChange,
}: {
  onCountChange?: (pendingCount: number) => void;
}) {
  const [month, setMonth] = useState(currentMonthKey());
  const [suggestions, setSuggestions] = useState<RecurringSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const hasLoaded = useRef(false);

  // Only show the loading state on first paint — confirming or
  // skipping a bill shouldn't blank out the other cards while it saves.
  function reload() {
    if (!hasLoaded.current) setLoading(true);
    api.recurringBills.getSuggestions(month).then((result) => {
      setSuggestions(result);
      setLoading(false);
      hasLoaded.current = true;
      if (month === currentMonthKey()) {
        onCountChange?.(result.filter((s) => s.status === 'pending').length);
      }
    });
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(reload, [month]);

  return (
    <div className="page">
      <div className="page__header">
        <div>
          <h2>Recurring bills</h2>
          <p className="text-muted">
            Rent, utilities and the usual suspects — suggested each month, never added without
            your say-so.
          </p>
        </div>
        <MonthSwitcher month={month} onChange={setMonth} />
      </div>

      {loading ? (
        <p className="text-muted">Loading…</p>
      ) : (
        <div className="bill-list">
          {suggestions.map((s) => (
            <BillCard key={s.bill.id} suggestion={s} month={month} onChanged={reload} />
          ))}
        </div>
      )}
    </div>
  );
}

function BillCard({
  suggestion,
  month,
  onChanged,
}: {
  suggestion: RecurringSuggestion;
  month: string;
  onChanged: () => void;
}) {
  const { bill, status } = suggestion;
  const [amount, setAmount] = useState(String(bill.amount));
  const [date, setDate] = useState(suggestion.suggestedDate);
  const [payerId, setPayerId] = useState(bill.defaultPayerId);
  const [busy, setBusy] = useState(false);

  async function confirm() {
    const parsed = Number(amount);
    if (!parsed || parsed <= 0) return;
    setBusy(true);
    await api.recurringBills.confirm(bill.id, month, { amount: parsed, date, payerId });
    setBusy(false);
    onChanged();
  }

  async function dismiss() {
    setBusy(true);
    await api.recurringBills.dismiss(bill.id, month);
    setBusy(false);
    onChanged();
  }

  async function undo() {
    setBusy(true);
    await api.recurringBills.undo(bill.id, month);
    setBusy(false);
    onChanged();
  }

  return (
    <div className={`bill-card bill-card--${status}`}>
      <div className="bill-card__head">
        <div>
          <h3>{bill.name}</h3>
          <CategoryTag categoryId={bill.categoryId} />
        </div>
        <StatusPill status={status} />
      </div>

      {status === 'pending' && (
        <>
          <p className="text-muted">
            Usually {formatCurrency(bill.amount)}, due around the {ordinal(bill.dueDayOfMonth)}.
          </p>
          <div className="form-grid form-grid--compact">
            <label>
              Amount
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </label>
            <label>
              Date
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
            <label>
              Paid by
              <select value={payerId} onChange={(e) => setPayerId(e.target.value)}>
                {MEMBERS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="form-actions form-actions--left">
            <button className="btn btn--primary" disabled={busy} onClick={confirm}>
              Confirm &amp; add
            </button>
            <button className="btn btn--ghost" disabled={busy} onClick={dismiss}>
              Skip this month
            </button>
          </div>
        </>
      )}

      {status === 'confirmed' && (
        <div className="bill-card__resolved">
          <p>
            Added <strong>{formatCurrency(suggestion.expenseAmount ?? bill.amount)}</strong> on{' '}
            {formatDateLabel(suggestion.expenseDate ?? suggestion.suggestedDate)}.
          </p>
          <button className="btn btn--ghost btn--small" disabled={busy} onClick={undo}>
            Undo
          </button>
        </div>
      )}

      {status === 'dismissed' && (
        <div className="bill-card__resolved">
          <p>Skipped for this month.</p>
          <button className="btn btn--ghost btn--small" disabled={busy} onClick={undo}>
            Undo
          </button>
        </div>
      )}
    </div>
  );
}

function StatusPill({ status }: { status: RecurringSuggestion['status'] }) {
  const label = status === 'pending' ? 'Needs confirmation' : status === 'confirmed' ? 'Added' : 'Skipped';
  return <span className={`status-pill status-pill--${status}`}>{label}</span>;
}

function ordinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}
