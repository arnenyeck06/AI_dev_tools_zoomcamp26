import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import { memberName } from '../api/constants';
import CategoryTag from '../components/CategoryTag';
import ExpenseForm from '../components/ExpenseForm';
import MonthSwitcher from '../components/MonthSwitcher';
import { currentMonthKey, formatCurrency, formatDateLabel } from '../lib/date';
import type { Expense, NewExpense } from '../api/types';

export default function Expenses() {
  const [month, setMonth] = useState(currentMonthKey());
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [panel, setPanel] = useState<'closed' | 'add' | Expense>('closed');
  const hasLoaded = useRef(false);

  // Only show the loading state on first paint — after that, refresh
  // the list quietly so edits and deletes don't flash the whole page.
  function reload() {
    if (!hasLoaded.current) setLoading(true);
    api.expenses.list({ month }).then((result) => {
      setExpenses(result);
      setLoading(false);
      hasLoaded.current = true;
    });
  }

  useEffect(reload, [month]);

  async function handleSubmit(values: NewExpense) {
    if (panel !== 'closed' && panel !== 'add') {
      await api.expenses.update(panel.id, values);
    } else {
      await api.expenses.create(values);
    }
    setPanel('closed');
    reload();
  }

  async function handleDelete(expense: Expense) {
    if (!window.confirm(`Delete this ${formatCurrency(expense.amount)} expense?`)) return;
    await api.expenses.remove(expense.id);
    reload();
  }

  const total = expenses.reduce((sum, e) => sum + e.amount, 0);

  return (
    <div className="page">
      <div className="page__header">
        <div>
          <h2>Expenses</h2>
          <p className="text-muted">Every dollar logged, assigned to whoever actually paid.</p>
        </div>
        <MonthSwitcher month={month} onChange={setMonth} />
      </div>

      <div className="card">
        <div className="card__row-between">
          <span className="text-muted">
            {expenses.length} expense{expenses.length === 1 ? '' : 's'} · {formatCurrency(total)} total
          </span>
          {panel === 'closed' && (
            <button className="btn btn--primary" onClick={() => setPanel('add')}>
              + Add expense
            </button>
          )}
        </div>

        {panel !== 'closed' && (
          <ExpenseForm
            key={panel === 'add' ? 'add' : panel.id}
            initial={panel === 'add' ? undefined : panel}
            submitLabel={panel === 'add' ? 'Add expense' : 'Save changes'}
            onSubmit={handleSubmit}
            onCancel={() => setPanel('closed')}
          />
        )}
      </div>

      {loading ? (
        <p className="text-muted">Loading…</p>
      ) : expenses.length === 0 ? (
        <p className="text-muted">No expenses logged this month yet.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Note</th>
                <th>Paid by</th>
                <th className="align-right">Amount</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {expenses.map((e) => (
                <tr key={e.id}>
                  <td>{formatDateLabel(e.date)}</td>
                  <td>
                    <CategoryTag categoryId={e.categoryId} />
                  </td>
                  <td className="text-muted">
                    {e.note ?? '—'}
                    {e.sourceBillId && <span className="pill">recurring</span>}
                  </td>
                  <td>{memberName(e.payerId)}</td>
                  <td className="align-right tabular">{formatCurrency(e.amount)}</td>
                  <td className="row-actions">
                    <button className="btn btn--ghost btn--small" onClick={() => setPanel(e)}>
                      Edit
                    </button>
                    <button className="btn btn--ghost btn--small" onClick={() => handleDelete(e)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
