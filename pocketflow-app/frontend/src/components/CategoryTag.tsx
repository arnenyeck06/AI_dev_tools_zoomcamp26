import { CATEGORIES } from '../api/constants';
import type { CategoryId } from '../api/types';

export function categoryColor(categoryId: CategoryId): string {
  const slot = CATEGORIES.find((c) => c.id === categoryId)?.slot ?? 8;
  return `var(--series-${slot})`;
}

export default function CategoryTag({ categoryId }: { categoryId: CategoryId }) {
  const category = CATEGORIES.find((c) => c.id === categoryId);
  return (
    <span className="category-tag">
      <span className="category-dot" style={{ background: categoryColor(categoryId) }} />
      {category?.name ?? categoryId}
    </span>
  );
}
