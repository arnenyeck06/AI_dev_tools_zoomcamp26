from fastapi import APIRouter, Depends

from ..schemas import Member
from ..store import Store, get_store

router = APIRouter(tags=["members"])


@router.get("/members", response_model=list[Member])
def list_members(store: Store = Depends(get_store)) -> list[Member]:
    return store.list_members()
