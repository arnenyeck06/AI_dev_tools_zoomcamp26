# Pydantic models matching the schemas in ../openapi.yaml.

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CategoryId = Literal[
    "rent",
    "utilities",
    "groceries",
    "dining",
    "transport",
    "entertainment",
    "health",
    "other",
]

BillStatus = Literal["pending", "confirmed", "dismissed"]

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
MONTH_PATTERN = r"^\d{4}-\d{2}$"


class Category(BaseModel):
    id: CategoryId
    name: str
    slot: int = Field(ge=1, le=8)


class Member(BaseModel):
    id: str
    name: str


class Expense(BaseModel):
    id: str
    amount: float = Field(gt=0)
    categoryId: CategoryId
    date: str = Field(pattern=DATE_PATTERN)
    payerId: str
    note: str | None = None
    sourceBillId: str | None = None


class NewExpense(BaseModel):
    amount: float = Field(gt=0)
    categoryId: CategoryId
    date: str = Field(pattern=DATE_PATTERN)
    payerId: str
    note: str | None = None


class ExpensePatch(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    categoryId: CategoryId | None = None
    date: str | None = Field(default=None, pattern=DATE_PATTERN)
    payerId: str | None = None
    note: str | None = None


class RecurringBillTemplate(BaseModel):
    id: str
    name: str
    categoryId: CategoryId
    amount: float = Field(gt=0)
    dueDayOfMonth: int = Field(ge=1, le=31)
    defaultPayerId: str


class RecurringSuggestion(BaseModel):
    bill: RecurringBillTemplate
    month: str = Field(pattern=MONTH_PATTERN)
    status: BillStatus
    expenseId: str | None = None
    expenseAmount: float | None = None
    expenseDate: str | None = None
    suggestedDate: str = Field(pattern=DATE_PATTERN)


class RecurringBillConfirmation(BaseModel):
    amount: float = Field(gt=0)
    date: str = Field(pattern=DATE_PATTERN)
    payerId: str
    note: str | None = None


class Budget(BaseModel):
    categoryId: CategoryId
    amount: float = Field(ge=0)


class BudgetAmount(BaseModel):
    amount: float = Field(ge=0)


class MonthlyCategoryTotals(BaseModel):
    month: str = Field(pattern=MONTH_PATTERN)
    totals: dict[CategoryId, float]
    total: float
