// Centralized backend access point.
//
// Every call the UI makes to "the backend" goes through the `api`
// object below. It talks to the FastAPI backend in `backend/app` over
// HTTP — no page should call `fetch` or simulate a request on its own.

import type {
  Budget,
  Category,
  Expense,
  ExpensePatch,
  Member,
  MonthlyCategoryTotals,
  NewExpense,
  RecurringBillTemplate,
  RecurringSuggestion,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json', ...init.headers } : init?.headers,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${res.status} ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function query(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined) as [string, string | number][];
  if (entries.length === 0) return '';
  return `?${new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()}`;
}

// --- API surface -------------------------------------------------------

export const api = {
  categories: {
    list(): Promise<Category[]> {
      return request('/categories');
    },
  },

  members: {
    list(): Promise<Member[]> {
      return request('/members');
    },
  },

  expenses: {
    list(opts?: { month?: string }): Promise<Expense[]> {
      return request(`/expenses${query({ month: opts?.month })}`);
    },

    create(input: NewExpense): Promise<Expense> {
      return request('/expenses', { method: 'POST', body: JSON.stringify(input) });
    },

    update(id: string, patch: ExpensePatch): Promise<Expense> {
      return request(`/expenses/${id}`, { method: 'PATCH', body: JSON.stringify(patch) });
    },

    remove(id: string): Promise<void> {
      return request(`/expenses/${id}`, { method: 'DELETE' });
    },
  },

  recurringBills: {
    list(): Promise<RecurringBillTemplate[]> {
      return request('/recurring-bills');
    },

    /** One suggestion per known bill, with its status for that month. */
    getSuggestions(month: string): Promise<RecurringSuggestion[]> {
      return request(`/recurring-bills/suggestions${query({ month })}`);
    },

    /** Confirms a bill for the month, creating the expense it represents. */
    confirm(
      billId: string,
      month: string,
      overrides: { amount: number; date: string; payerId: string; note?: string },
    ): Promise<Expense> {
      return request(`/recurring-bills/${billId}/confirm${query({ month })}`, {
        method: 'POST',
        body: JSON.stringify(overrides),
      });
    },

    dismiss(billId: string, month: string): Promise<void> {
      return request(`/recurring-bills/${billId}/dismiss${query({ month })}`, { method: 'POST' });
    },

    /** Reverts a confirmed or dismissed bill back to pending for that month. */
    undo(billId: string, month: string): Promise<void> {
      return request(`/recurring-bills/${billId}/undo${query({ month })}`, { method: 'POST' });
    },
  },

  budgets: {
    list(): Promise<Budget[]> {
      return request('/budgets');
    },

    set(categoryId: Budget['categoryId'], amount: number): Promise<Budget> {
      return request(`/budgets/${categoryId}`, { method: 'PUT', body: JSON.stringify({ amount }) });
    },
  },

  trends: {
    /** Last `count` months, oldest first, ending at the current month. */
    monthly(count: number): Promise<MonthlyCategoryTotals[]> {
      return request(`/trends/monthly${query({ count })}`);
    },
  },
};
