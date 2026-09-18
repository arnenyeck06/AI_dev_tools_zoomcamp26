import { useState } from 'react';
import CategoryTag from './CategoryTag';
import Meter from './Meter';
import { formatCurrency } from '../lib/date';
import type { CategoryId } from '../api/types';

export default function BudgetRow({
  categoryId,
  budget,
  actual,
  editable = false,
  onSaveBudget,
}: {
  categoryId: CategoryId;
  budget: number;
  actual: number;
  editable?: boolean;
  onSaveBudget?: (amount: number) => void;
}) {
  const [draft, setDraft] = useState(String(budget));
  const remaining = budget - actual;
  const pct = budget > 0 ? Math.round((actual / budget) * 100) : 0;

  function commit() {
    const amount = Number(draft);
    if (!Number.isNaN(amount) && amount >= 0 && amount !== budget) {
      onSaveBudget?.(amount);
    } else {
      setDraft(String(budget));
    }
  }

  return (
    <div className="budget-row">
      <div className="budget-row__head">
        <CategoryTag categoryId={categoryId} />
        {editable ? (
          <span className="budget-edit">
            <span className="budget-edit__currency">$</span>
            <input
              type="number"
              min={0}
              step="1"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={commit}
              onKeyDown={(e) => e.key === 'Enter' && (e.currentTarget as HTMLInputElement).blur()}
              aria-label={`Monthly budget for ${categoryId}`}
            />
            <span className="budget-edit__unit">/mo</span>
          </span>
        ) : (
          <span className="text-muted">{formatCurrency(budget)} budget</span>
        )}
      </div>
      <Meter value={actual} max={budget} />
      <div className="budget-row__foot">
        <span>
          {formatCurrency(actual)} of {formatCurrency(budget)} ({pct}%)
        </span>
        <span className={remaining < 0 ? 'text-critical' : 'text-muted'}>
          {remaining >= 0
            ? `${formatCurrency(remaining)} left`
            : `${formatCurrency(-remaining)} over`}
        </span>
      </div>
    </div>
  );
}
