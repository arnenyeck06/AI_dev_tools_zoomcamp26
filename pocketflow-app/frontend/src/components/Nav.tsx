export type Page = 'dashboard' | 'expenses' | 'recurring' | 'budgets' | 'trends';

const TABS: { id: Page; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'expenses', label: 'Expenses' },
  { id: 'recurring', label: 'Recurring bills' },
  { id: 'budgets', label: 'Budgets' },
  { id: 'trends', label: 'Trends' },
];

export default function Nav({
  page,
  onNavigate,
  recurringBadge,
}: {
  page: Page;
  onNavigate: (page: Page) => void;
  recurringBadge?: number;
}) {
  return (
    <header className="app-header">
      <div className="app-header__brand">
        <span className="app-header__logo">PocketFlow</span>
      </div>
      <nav className="app-nav">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`app-nav__tab ${page === tab.id ? 'app-nav__tab--active' : ''}`}
            onClick={() => onNavigate(tab.id)}
          >
            {tab.label}
            {tab.id === 'recurring' && !!recurringBadge && (
              <span className="app-nav__badge">{recurringBadge}</span>
            )}
          </button>
        ))}
      </nav>
    </header>
  );
}
