# In-memory mock database. Mirrors frontend/src/api/{constants,mockData,client}.ts
# so the two mocks agree on shape and seed data. Swap this module out for a
# real database later without touching the routers, which only call `store`.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from . import dates
from .schemas import (
    Budget,
    Category,
    CategoryId,
    Expense,
    ExpensePatch,
    Member,
    MonthlyCategoryTotals,
    NewExpense,
    RecurringBillConfirmation,
    RecurringBillTemplate,
    RecurringSuggestion,
)

CATEGORIES: list[Category] = [
    Category(id="rent", name="Rent", slot=1),
    Category(id="utilities", name="Utilities", slot=2),
    Category(id="groceries", name="Groceries", slot=3),
    Category(id="dining", name="Dining", slot=4),
    Category(id="transport", name="Transport", slot=5),
    Category(id="entertainment", name="Entertainment", slot=6),
    Category(id="health", name="Health", slot=7),
    Category(id="other", name="Other", slot=8),
]

MEMBERS: list[Member] = [
    Member(id="m1", name="Alex"),
    Member(id="m2", name="Sam"),
]

RECURRING_BILLS: list[RecurringBillTemplate] = [
    RecurringBillTemplate(
        id="rb1", name="Rent", categoryId="rent", amount=1800,
        dueDayOfMonth=1, defaultPayerId="m1",
    ),
    RecurringBillTemplate(
        id="rb2", name="Electric & Water", categoryId="utilities", amount=95,
        dueDayOfMonth=20, defaultPayerId="m2",
    ),
    RecurringBillTemplate(
        id="rb3", name="Streaming Bundle", categoryId="entertainment", amount=42,
        dueDayOfMonth=3, defaultPayerId="m2",
    ),
]

SEED_BUDGETS: list[Budget] = [
    Budget(categoryId="rent", amount=1800),
    Budget(categoryId="utilities", amount=150),
    Budget(categoryId="groceries", amount=500),
    Budget(categoryId="dining", amount=200),
    Budget(categoryId="transport", amount=150),
    Budget(categoryId="entertainment", amount=50),
    Budget(categoryId="health", amount=80),
    Budget(categoryId="other", amount=100),
]


@dataclass
class _SeedRow:
    day: int
    category_id: CategoryId
    amount: float
    payer_id: str
    note: str | None = None
    source_bill_id: str | None = None


def _month_rows(month: str, rows: list[_SeedRow]) -> list[Expense]:
    return [
        Expense(
            id=f"{month}-{i}",
            amount=row.amount,
            categoryId=row.category_id,
            date=f"{month}-{row.day:02d}",
            payerId=row.payer_id,
            note=row.note,
            sourceBillId=row.source_bill_id,
        )
        for i, row in enumerate(rows)
    ]


def _seed_expenses() -> list[Expense]:
    # Five full months of history (April-August 2026) plus a partial
    # current month (September, up to the 16th) so trends has history
    # and budgets has a realistic in-progress month to compare against.
    #
    # The current month's rent/utilities/streaming bill are deliberately
    # NOT seeded as expenses -- they show up as pending recurring-bill
    # suggestions instead, exercising the "confirm before adding" flow.
    return [
        *_month_rows("2026-04", [
            _SeedRow(1, "rent", 1800, "m1", source_bill_id="rb1"),
            _SeedRow(3, "entertainment", 42, "m2", source_bill_id="rb3"),
            _SeedRow(6, "groceries", 128.4, "m1"),
            _SeedRow(9, "dining", 54.2, "m2", note="Sushi night"),
            _SeedRow(12, "transport", 60, "m1", note="Gas"),
            _SeedRow(14, "groceries", 96.75, "m2"),
            _SeedRow(19, "utilities", 88.1, "m2", source_bill_id="rb2"),
            _SeedRow(22, "groceries", 110.3, "m1"),
            _SeedRow(25, "dining", 32.5, "m1"),
            _SeedRow(28, "health", 45, "m2", note="Pharmacy"),
        ]),
        *_month_rows("2026-05", [
            _SeedRow(1, "rent", 1800, "m1", source_bill_id="rb1"),
            _SeedRow(3, "entertainment", 42, "m2", source_bill_id="rb3"),
            _SeedRow(5, "groceries", 132.1, "m2"),
            _SeedRow(10, "dining", 210, "m1", note="Anniversary dinner"),
            _SeedRow(13, "transport", 55, "m1"),
            _SeedRow(17, "groceries", 101.6, "m1"),
            _SeedRow(20, "utilities", 132.4, "m2", note="AC running", source_bill_id="rb2"),
            _SeedRow(23, "groceries", 89.9, "m2"),
            _SeedRow(27, "other", 60, "m1", note="Birthday gift for niece"),
        ]),
        *_month_rows("2026-06", [
            _SeedRow(1, "rent", 1800, "m1", source_bill_id="rb1"),
            _SeedRow(3, "entertainment", 42, "m2", source_bill_id="rb3"),
            _SeedRow(7, "groceries", 118.2, "m1"),
            _SeedRow(9, "dining", 48, "m2"),
            _SeedRow(11, "transport", 72.3, "m2", note="Car repair - oil change"),
            _SeedRow(15, "groceries", 95.4, "m2"),
            _SeedRow(18, "utilities", 91.75, "m2", source_bill_id="rb2"),
            _SeedRow(21, "dining", 265, "m1", note="Birthday splurge dinner"),
            _SeedRow(24, "groceries", 122.1, "m1"),
            _SeedRow(29, "health", 30, "m2"),
        ]),
        *_month_rows("2026-07", [
            _SeedRow(1, "rent", 1800, "m1", source_bill_id="rb1"),
            _SeedRow(3, "entertainment", 42, "m2", source_bill_id="rb3"),
            _SeedRow(5, "groceries", 140.5, "m1"),
            _SeedRow(8, "dining", 60.25, "m2"),
            _SeedRow(12, "transport", 58, "m1"),
            _SeedRow(16, "groceries", 99.1, "m2"),
            _SeedRow(19, "utilities", 145.9, "m2", note="Heat wave - AC spike", source_bill_id="rb2"),
            _SeedRow(22, "groceries", 105.75, "m1"),
            _SeedRow(26, "other", 85, "m2", note="New phone case + accessories"),
            _SeedRow(30, "dining", 40, "m1"),
        ]),
        *_month_rows("2026-08", [
            _SeedRow(1, "rent", 1800, "m1", source_bill_id="rb1"),
            _SeedRow(3, "entertainment", 42, "m2", source_bill_id="rb3"),
            _SeedRow(6, "groceries", 133.85, "m2"),
            _SeedRow(9, "dining", 72.4, "m1"),
            _SeedRow(13, "transport", 64, "m2"),
            _SeedRow(17, "groceries", 108.2, "m1"),
            _SeedRow(20, "utilities", 99.3, "m2", source_bill_id="rb2"),
            _SeedRow(23, "groceries", 91.55, "m2"),
            _SeedRow(26, "dining", 38.6, "m1"),
            _SeedRow(29, "health", 55, "m1", note="Dentist copay"),
        ]),
        *_month_rows("2026-09", [
            _SeedRow(2, "groceries", 102.3, "m1"),
            _SeedRow(5, "dining", 45.6, "m2"),
            _SeedRow(8, "transport", 62, "m1"),
            _SeedRow(11, "groceries", 88.9, "m2"),
            _SeedRow(14, "dining", 30, "m1"),
            _SeedRow(16, "other", 25.5, "m2", note="Birthday card + wrapping"),
        ]),
    ]


class NotFoundError(Exception):
    pass


@dataclass
class _Dismissal:
    bill_id: str
    month: str


@dataclass
class Store:
    expenses: list[Expense] = field(default_factory=_seed_expenses)
    budgets: list[Budget] = field(default_factory=lambda: list(SEED_BUDGETS))
    dismissals: list[_Dismissal] = field(default_factory=list)

    def reset(self) -> None:
        self.expenses = _seed_expenses()
        self.budgets = list(SEED_BUDGETS)
        self.dismissals = []

    # -- reference data --------------------------------------------------

    def list_categories(self) -> list[Category]:
        return list(CATEGORIES)

    def list_members(self) -> list[Member]:
        return list(MEMBERS)

    # -- expenses ----------------------------------------------------------

    def list_expenses(self, month: str | None = None) -> list[Expense]:
        result = self.expenses
        if month is not None:
            result = [e for e in result if dates.month_key_of(e.date) == month]
        return sorted(result, key=lambda e: e.date, reverse=True)

    def create_expense(self, input_: NewExpense) -> Expense:
        created = Expense(id=str(uuid.uuid4()), **input_.model_dump())
        self.expenses.append(created)
        return created

    def _find_expense(self, expense_id: str) -> Expense:
        for e in self.expenses:
            if e.id == expense_id:
                return e
        raise NotFoundError(f"Expense {expense_id} not found")

    def update_expense(self, expense_id: str, patch: ExpensePatch) -> Expense:
        existing = self._find_expense(expense_id)
        updated = existing.model_copy(
            update=patch.model_dump(exclude_unset=True)
        )
        self.expenses = [updated if e.id == expense_id else e for e in self.expenses]
        return updated

    def delete_expense(self, expense_id: str) -> None:
        self._find_expense(expense_id)
        self.expenses = [e for e in self.expenses if e.id != expense_id]

    # -- recurring bills -----------------------------------------------

    def list_recurring_bills(self) -> list[RecurringBillTemplate]:
        return list(RECURRING_BILLS)

    def _find_bill(self, bill_id: str) -> RecurringBillTemplate:
        for b in RECURRING_BILLS:
            if b.id == bill_id:
                return b
        raise NotFoundError(f"Recurring bill {bill_id} not found")

    def _is_dismissed(self, bill_id: str, month: str) -> bool:
        return any(
            d.bill_id == bill_id and d.month == month for d in self.dismissals
        )

    def get_recurring_suggestions(self, month: str) -> list[RecurringSuggestion]:
        result = []
        for bill in RECURRING_BILLS:
            suggested_date = dates.date_in_month(month, bill.dueDayOfMonth)
            linked = next(
                (
                    e
                    for e in self.expenses
                    if e.sourceBillId == bill.id and dates.month_key_of(e.date) == month
                ),
                None,
            )
            if linked is not None:
                result.append(
                    RecurringSuggestion(
                        bill=bill,
                        month=month,
                        status="confirmed",
                        expenseId=linked.id,
                        expenseAmount=linked.amount,
                        expenseDate=linked.date,
                        suggestedDate=suggested_date,
                    )
                )
            elif self._is_dismissed(bill.id, month):
                result.append(
                    RecurringSuggestion(
                        bill=bill, month=month, status="dismissed",
                        suggestedDate=suggested_date,
                    )
                )
            else:
                result.append(
                    RecurringSuggestion(
                        bill=bill, month=month, status="pending",
                        suggestedDate=suggested_date,
                    )
                )
        return result

    def confirm_recurring_bill(
        self, bill_id: str, month: str, overrides: RecurringBillConfirmation
    ) -> Expense:
        bill = self._find_bill(bill_id)
        created = Expense(
            id=str(uuid.uuid4()),
            categoryId=bill.categoryId,
            amount=overrides.amount,
            date=overrides.date,
            payerId=overrides.payerId,
            note=overrides.note,
            sourceBillId=bill.id,
        )
        self.expenses.append(created)
        self.dismissals = [
            d for d in self.dismissals if not (d.bill_id == bill_id and d.month == month)
        ]
        return created

    def dismiss_recurring_bill(self, bill_id: str, month: str) -> None:
        self._find_bill(bill_id)
        if not self._is_dismissed(bill_id, month):
            self.dismissals.append(_Dismissal(bill_id=bill_id, month=month))

    def undo_recurring_bill(self, bill_id: str, month: str) -> None:
        self._find_bill(bill_id)
        self.expenses = [
            e
            for e in self.expenses
            if not (e.sourceBillId == bill_id and dates.month_key_of(e.date) == month)
        ]
        self.dismissals = [
            d for d in self.dismissals if not (d.bill_id == bill_id and d.month == month)
        ]

    # -- budgets -------------------------------------------------------

    def list_budgets(self) -> list[Budget]:
        return list(self.budgets)

    def set_budget(self, category_id: CategoryId, amount: float) -> Budget:
        updated = Budget(categoryId=category_id, amount=amount)
        if any(b.categoryId == category_id for b in self.budgets):
            self.budgets = [
                updated if b.categoryId == category_id else b for b in self.budgets
            ]
        else:
            self.budgets.append(updated)
        return updated

    # -- trends ----------------------------------------------------------

    def monthly_trends(self, count: int) -> list[MonthlyCategoryTotals]:
        current_month = dates.current_month_key()
        months = [dates.add_months(current_month, -i) for i in range(count - 1, -1, -1)]

        result = []
        for month in months:
            totals: dict[CategoryId, float] = {c.id: 0.0 for c in CATEGORIES}
            total = 0.0
            for e in self.expenses:
                if dates.month_key_of(e.date) == month:
                    totals[e.categoryId] += e.amount
                    total += e.amount
            result.append(MonthlyCategoryTotals(month=month, totals=totals, total=total))
        return result


store = Store()


def get_store() -> Store:
    return store
