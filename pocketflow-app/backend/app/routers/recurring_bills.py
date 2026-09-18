from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..schemas import (
    MONTH_PATTERN,
    Expense,
    RecurringBillConfirmation,
    RecurringBillTemplate,
    RecurringSuggestion,
)
from ..store import NotFoundError, Store, get_store

router = APIRouter(prefix="/recurring-bills", tags=["recurring-bills"])

MonthQuery = Query(pattern=MONTH_PATTERN)


@router.get("", response_model=list[RecurringBillTemplate])
def list_recurring_bills(store: Store = Depends(get_store)) -> list[RecurringBillTemplate]:
    return store.list_recurring_bills()


@router.get("/suggestions", response_model=list[RecurringSuggestion])
def get_recurring_suggestions(
    month: str = MonthQuery, store: Store = Depends(get_store)
) -> list[RecurringSuggestion]:
    return store.get_recurring_suggestions(month)


@router.post(
    "/{bill_id}/confirm", response_model=Expense, status_code=status.HTTP_201_CREATED
)
def confirm_recurring_bill(
    bill_id: str,
    confirmation: RecurringBillConfirmation,
    month: str = MonthQuery,
    store: Store = Depends(get_store),
) -> Expense:
    try:
        return store.confirm_recurring_bill(bill_id, month, confirmation)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{bill_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_recurring_bill(
    bill_id: str, month: str = MonthQuery, store: Store = Depends(get_store)
) -> None:
    try:
        store.dismiss_recurring_bill(bill_id, month)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{bill_id}/undo", status_code=status.HTTP_204_NO_CONTENT)
def undo_recurring_bill(
    bill_id: str, month: str = MonthQuery, store: Store = Depends(get_store)
) -> None:
    try:
        store.undo_recurring_bill(bill_id, month)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
