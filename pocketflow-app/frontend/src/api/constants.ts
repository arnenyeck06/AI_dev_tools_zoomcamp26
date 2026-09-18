import type { Category, Member } from './types';

// Fixed reference data. The MVP doesn't call for custom categories or
// household membership management, so these are static rather than
// another CRUD surface.

export const CATEGORIES: Category[] = [
  { id: 'rent', name: 'Rent', slot: 1 },
  { id: 'utilities', name: 'Utilities', slot: 2 },
  { id: 'groceries', name: 'Groceries', slot: 3 },
  { id: 'dining', name: 'Dining', slot: 4 },
  { id: 'transport', name: 'Transport', slot: 5 },
  { id: 'entertainment', name: 'Entertainment', slot: 6 },
  { id: 'health', name: 'Health', slot: 7 },
  { id: 'other', name: 'Other', slot: 8 },
];

export const MEMBERS: Member[] = [
  { id: 'm1', name: 'Alex' },
  { id: 'm2', name: 'Sam' },
];

export function memberName(id: string): string {
  return MEMBERS.find((m) => m.id === id)?.name ?? 'Unknown';
}
