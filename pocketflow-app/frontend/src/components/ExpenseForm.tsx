import { useState } from 'react';
import { CATEGORIES, MEMBERS } from '../api/constants';
import { todayISO } from '../lib/date';
import type { CategoryId, Expense, NewExpense } from '../api/types';

export interface ExpenseFormValues {
  amount: number;
  categoryId: CategoryId;
  date: string;
  payerId: string;
  note?: string;
}

export default function ExpenseForm({
  initial,
  onSubmit,
  onCancel,
  submitLabel = 'Add expense',
}: {
  initial?: Expense;
  onSubmit: (values: NewExpense) => void;
  onCancel: () => void;
  submitLabel?: string;
}) {
  const [amount, setAmount] = useState(initial ? String(initial.amount) : '');
  const [categoryId, setCategoryId] = useState<CategoryId>(initial?.categoryId ?? CATEGORIES[0].id);
  const [date, setDate] = useState(initial?.date ?? todayISO());
  const [payerId, setPayerId] = useState(initial?.payerId ?? MEMBERS[0].id);
  const [note, setNote] = useState(initial?.note ?? '');
  const [error, setError] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = Number(amount);
    if (!amount || Number.isNaN(parsed) || parsed <= 0) {
      setError('Enter an amount greater than 0.');
      return;
    }
    if (!date) {
      setError('Pick a date.');
      return;
    }
    onSubmit({
      amount: parsed,
      categoryId,
      date,
      payerId,
      note: note.trim() || undefined,
    });
  }

  return (
    <form className="expense-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        <label>
          Amount
          <input
            type="number"
            min="0.01"
            step="0.01"
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            autoFocus
          />
        </label>
        <label>
          Category
          <select value={categoryId} onChange={(e) => setCategoryId(e.target.value as CategoryId)}>
            {CATEGORIES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
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
        <label className="form-grid__wide">
          Note <span className="text-muted">(optional)</span>
          <input
            type="text"
            placeholder="e.g. birthday splurge"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>
      </div>
      {error && <p className="form-error">{error}</p>}
      <div className="form-actions">
        <button type="button" className="btn btn--ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn--primary">
          {submitLabel}
        </button>
      </div>
    </form>
  );
}
