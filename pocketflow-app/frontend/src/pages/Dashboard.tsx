import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CATEGORIES } from '../api/constants';
import BudgetRow from '../components/BudgetRow';
import StatTile from '../components/StatTile';
import type { Page } from '../components/Nav';
import { currentMonthKey, formatCurrency, formatMonthLabel } from '../lib/date';
import type { Budget, CategoryId, RecurringSuggestion } from '../api/types';

export default function Dashboard({ onNavigate }: { onNavigate: (page: Page) => void }) {
  const month = currentMonthKey();
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [actuals, setActuals] = useState<Record<CategoryId, number>>({} as Record<CategoryId, number>);
  const [suggestions, setSuggestions] = useState<RecurringSuggestion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.budgets.list(),
      api.expenses.list({ month }),
      api.recurringBills.getSuggestions(month),
    ]).then(([budgetList, expenses, billSuggestions]) => {
      const totals = {} as Record<CategoryId, number>;
      for (const c of CATEGORIES) totals[c.id] = 0;
      for (const e of expenses) totals[e.categoryId] += e.amount;
      setBudgets(budgetList);
      setActuals(totals);
      setSuggestions(billSuggestions);
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalBudget = budgets.reduce((sum, b) => sum + b.amount, 0);
  const totalActual = Object.values(actuals).reduce((sum, v) => sum + v, 0);
  const pending = suggestions.filter((s) => s.status === 'pending');

  return (
    <div className="page">
      <div className="page__header">
        <div>
          <h2>Dashboard</h2>
          <p className="text-muted">{formatMonthLabel(month)} at a glance.</p>
        </div>
      </div>

      {loading ? (
        <p className="text-muted">Loading…</p>
      ) : (
        <>
          {pending.length > 0 && (
            <div className="banner">
              <span>
                {pending.length} recurring bill{pending.length === 1 ? '' : 's'} need
                {pending.length === 1 ? 's' : ''} confirmation for {formatMonthLabel(month)}.
              </span>
              <button className="btn btn--primary btn--small" onClick={() => onNavigate('recurring')}>
                Review
              </button>
            </div>
          )}

          <div className="stat-row">
            <StatTile label="Spent this month" value={formatCurrency(totalActual)} />
            <StatTile label="Monthly budget" value={formatCurrency(totalBudget)} />
            <StatTile
              label="Remaining"
              value={formatCurrency(totalBudget - totalActual)}
              tone={totalActual > totalBudget ? 'critical' : 'good'}
            />
            <StatTile
              label="Pending bills"
              value={String(pending.length)}
              sub={pending.length > 0 ? 'awaiting confirmation' : 'all caught up'}
            />
          </div>

          <div className="page__header">
            <h3>Budget vs. actual</h3>
            <button className="btn btn--ghost btn--small" onClick={() => onNavigate('budgets')}>
              Manage budgets
            </button>
          </div>
          <div className="budget-grid">
            {CATEGORIES.map((c) => {
              const budget = budgets.find((b) => b.categoryId === c.id)?.amount ?? 0;
              return (
                <BudgetRow key={c.id} categoryId={c.id} budget={budget} actual={actuals[c.id] ?? 0} />
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
