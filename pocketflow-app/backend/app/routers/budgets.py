from fastapi import APIRouter, Depends

from ..schemas import Budget, BudgetAmount, CategoryId
from ..store import Store, get_store

router = APIRouter(tags=["budgets"])


@router.get("/budgets", response_model=list[Budget])
def list_budgets(store: Store = Depends(get_store)) -> list[Budget]:
    return store.list_budgets()


@router.put("/budgets/{category_id}", response_model=Budget)
def set_budget(
    category_id: CategoryId, body: BudgetAmount, store: Store = Depends(get_store)
) -> Budget:
    return store.set_budget(category_id, body.amount)
