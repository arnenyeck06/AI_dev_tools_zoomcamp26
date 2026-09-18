import { useEffect, useState } from 'react';
import { api } from './api/client';
import Nav, { type Page } from './components/Nav';
import Dashboard from './pages/Dashboard';
import Expenses from './pages/Expenses';
import RecurringBills from './pages/RecurringBills';
import Budgets from './pages/Budgets';
import Trends from './pages/Trends';
import { currentMonthKey } from './lib/date';
import './App.css';

export default function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [pendingBills, setPendingBills] = useState(0);

  // Populate the nav badge up front, without requiring a visit to the
  // Recurring Bills page first.
  useEffect(() => {
    api.recurringBills
      .getSuggestions(currentMonthKey())
      .then((result) => setPendingBills(result.filter((s) => s.status === 'pending').length));
  }, [page]);

  return (
    <div className="app-shell">
      <Nav page={page} onNavigate={setPage} recurringBadge={pendingBills} />
      <main className="app-main">
        {page === 'dashboard' && <Dashboard onNavigate={setPage} />}
        {page === 'expenses' && <Expenses />}
        {page === 'recurring' && <RecurringBills onCountChange={setPendingBills} />}
        {page === 'budgets' && <Budgets />}
        {page === 'trends' && <Trends />}
      </main>
    </div>
  );
}
