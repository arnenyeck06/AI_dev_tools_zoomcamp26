from fastapi import APIRouter, Depends, Query

from ..schemas import MonthlyCategoryTotals
from ..store import Store, get_store

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/monthly", response_model=list[MonthlyCategoryTotals])
def get_monthly_trends(
    count: int = Query(ge=1), store: Store = Depends(get_store)
) -> list[MonthlyCategoryTotals]:
    return store.monthly_trends(count)
