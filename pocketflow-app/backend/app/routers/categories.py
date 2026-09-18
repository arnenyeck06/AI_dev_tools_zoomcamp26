from fastapi import APIRouter, Depends

from ..schemas import Category
from ..store import Store, get_store

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[Category])
def list_categories(store: Store = Depends(get_store)) -> list[Category]:
    return store.list_categories()
