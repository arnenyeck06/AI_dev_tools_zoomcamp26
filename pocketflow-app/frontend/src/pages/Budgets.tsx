import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import { CATEGORIES } from '../api/constants';
import BudgetRow from '../components/BudgetRow';
import MonthSwitcher from '../components/MonthSwitcher';
import { currentMonthKey, formatCurrency } from '../lib/date';
import type { Budget, CategoryId } from '../api/types';

export default function Budgets() {
  const [month, setMonth] = useState(currentMonthKey());
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [actuals, setActuals] = useState<Record<CategoryId, number>>({} as Record<CategoryId, number>);
  const [loading, setLoading] = useState(true);
  const hasLoaded = useRef(false);

  // Only show the loading state on first paint — saving a budget
  // shouldn't blank out the whole grid while it refreshes.
  function reload() {
    if (!hasLoaded.current) setLoading(true);
    Promise.all([api.budgets.list(), api.expenses.list({ month })]).then(([budgetList, expenses]) => {
      const totals = {} as Record<CategoryId, number>;
      for (const c of CATEGORIES) totals[c.id] = 0;
      for (const e of expenses) totals[e.categoryId] += e.amount;
      setBudgets(budgetList);
      setActuals(totals);
      setLoading(false);
      hasLoaded.current = true;
    });
  }

  useEffect(reload, [month]);

  async function handleSave(categoryId: CategoryId, amount: number) {
    await api.budgets.set(categoryId, amount);
    reload();
  }

  const totalBudget = budgets.reduce((sum, b) => sum + b.amount, 0);
  const totalActual = Object.values(actuals).reduce((sum, v) => sum + v, 0);

  return (
    <div className="page">
      <div className="page__header">
        <div>
          <h2>Budgets</h2>
          <p className="text-muted">One number per category, checked against what actually went out.</p>
        </div>
        <MonthSwitcher month={month} onChange={setMonth} />
      </div>

      {loading ? (
        <p className="text-muted">Loading…</p>
      ) : (
        <>
          <p className="text-muted">
            {formatCurrency(totalActual)} spent of {formatCurrency(totalBudget)} budgeted this month.
          </p>
          <div className="budget-grid">
            {CATEGORIES.map((c) => {
              const budget = budgets.find((b) => b.categoryId === c.id)?.amount ?? 0;
              return (
                <BudgetRow
                  key={c.id}
                  categoryId={c.id}
                  budget={budget}
                  actual={actuals[c.id] ?? 0}
                  editable
                  onSaveBudget={(amount) => handleSave(c.id, amount)}
                />
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
