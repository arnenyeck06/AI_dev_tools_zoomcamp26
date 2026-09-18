// Shared domain types for the PocketFlow API layer.
// This is the contract the real backend will eventually implement —
// today it's served entirely by the mock in `client.ts`.

export type CategoryId =
  | 'rent'
  | 'utilities'
  | 'groceries'
  | 'dining'
  | 'transport'
  | 'entertainment'
  | 'health'
  | 'other';

export interface Category {
  id: CategoryId;
  name: string;
  /** 1-8, fixed order — used to pick a stable chart color per category. */
  slot: number;
}

export interface Member {
  id: string;
  name: string;
}

export interface Expense {
  id: string;
  amount: number;
  categoryId: CategoryId;
  /** ISO date, yyyy-mm-dd */
  date: string;
  payerId: string;
  note?: string;
  /** Set when this expense was created by confirming a recurring bill. */
  sourceBillId?: string;
}

export type NewExpense = Omit<Expense, 'id' | 'sourceBillId'>;
export type ExpensePatch = Partial<Omit<Expense, 'id'>>;

export interface RecurringBillTemplate {
  id: string;
  name: string;
  categoryId: CategoryId;
  amount: number;
  dueDayOfMonth: number;
  defaultPayerId: string;
}

export type BillStatus = 'pending' | 'confirmed' | 'dismissed';

export interface RecurringSuggestion {
  bill: RecurringBillTemplate;
  /** yyyy-mm */
  month: string;
  status: BillStatus;
  /** Present once confirmed — the expense it created. */
  expenseId?: string;
  expenseAmount?: number;
  expenseDate?: string;
  /** Default date for the confirmation form, derived from dueDayOfMonth. */
  suggestedDate: string;
}

export interface Budget {
  categoryId: CategoryId;
  /** Monthly budget amount, applied every month until changed. */
  amount: number;
}

export interface MonthlyCategoryTotals {
  /** yyyy-mm */
  month: string;
  totals: Record<CategoryId, number>;
  total: number;
}
