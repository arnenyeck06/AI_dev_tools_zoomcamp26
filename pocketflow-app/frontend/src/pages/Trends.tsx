import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CATEGORIES } from '../api/constants';
import { categoryColor } from '../components/CategoryTag';
import { formatCurrency, formatMonthLabel, formatMonthShort } from '../lib/date';
import type { MonthlyCategoryTotals } from '../api/types';

const MONTHS_SHOWN = 6;
const CHART_HEIGHT = 260;

export default function Trends() {
  const [data, setData] = useState<MonthlyCategoryTotals[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'chart' | 'table'>('chart');

  useEffect(() => {
    api.trends.monthly(MONTHS_SHOWN).then((result) => {
      setData(result);
      setLoading(false);
    });
  }, []);

  const maxTotal = Math.max(1, ...data.map((d) => d.total));

  return (
    <div className="page">
      <div className="page__header">
        <div>
          <h2>Trends</h2>
          <p className="text-muted">
            Month-over-month spending by category — steady bars are the recurring bills, spikes
            are the one-off splurges.
          </p>
        </div>
        <div className="view-toggle">
          <button
            className={`btn btn--ghost btn--small ${view === 'chart' ? 'btn--active' : ''}`}
            onClick={() => setView('chart')}
          >
            Chart
          </button>
          <button
            className={`btn btn--ghost btn--small ${view === 'table' ? 'btn--active' : ''}`}
            onClick={() => setView('table')}
          >
            Table
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-muted">Loading…</p>
      ) : view === 'chart' ? (
        <div className="card">
          <div className="trend-chart" style={{ height: CHART_HEIGHT }}>
            {data.map((month) => (
              <div className="trend-chart__col" key={month.month}>
                <div className="trend-chart__bar">
                  {CATEGORIES.filter((c) => month.totals[c.id] > 0).map((c) => {
                    const amount = month.totals[c.id];
                    const height = (amount / maxTotal) * CHART_HEIGHT;
                    return (
                      <div
                        key={c.id}
                        className="bar-segment"
                        style={{ height, background: categoryColor(c.id) }}
                      >
                        <div className="bar-segment__tooltip">
                          {c.name}: {formatCurrency(amount)}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="trend-chart__label">{formatMonthShort(month.month)}</div>
                <div className="trend-chart__total tabular">{formatCurrency(month.total)}</div>
              </div>
            ))}
          </div>
          <div className="legend">
            {CATEGORIES.map((c) => (
              <span className="legend__item" key={c.id}>
                <span className="category-dot" style={{ background: categoryColor(c.id) }} />
                {c.name}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Month</th>
                {CATEGORIES.map((c) => (
                  <th key={c.id} className="align-right">
                    {c.name}
                  </th>
                ))}
                <th className="align-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {data.map((month) => (
                <tr key={month.month}>
                  <td>{formatMonthLabel(month.month)}</td>
                  {CATEGORIES.map((c) => (
                    <td key={c.id} className="align-right tabular">
                      {month.totals[c.id] > 0 ? formatCurrency(month.totals[c.id]) : '—'}
                    </td>
                  ))}
                  <td className="align-right tabular">
                    <strong>{formatCurrency(month.total)}</strong>
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
