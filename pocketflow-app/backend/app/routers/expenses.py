from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..schemas import Expense, ExpensePatch, MONTH_PATTERN, NewExpense
from ..store import NotFoundError, Store, get_store

router = APIRouter(tags=["expenses"])


@router.get("/expenses", response_model=list[Expense])
def list_expenses(
    month: str | None = Query(default=None, pattern=MONTH_PATTERN),
    store: Store = Depends(get_store),
) -> list[Expense]:
    return store.list_expenses(month=month)


@router.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED)
def create_expense(input_: NewExpense, store: Store = Depends(get_store)) -> Expense:
    return store.create_expense(input_)


@router.patch("/expenses/{expense_id}", response_model=Expense)
def update_expense(
    expense_id: str, patch: ExpensePatch, store: Store = Depends(get_store)
) -> Expense:
    try:
        return store.update_expense(expense_id, patch)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: str, store: Store = Depends(get_store)) -> None:
    try:
        store.delete_expense(expense_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
