"""Food order queue API: customers place orders, staff serve them first in, first out."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, func, select

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///orders.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class OrderCreate(SQLModel):
    customer_name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=7, max_length=20)
    item: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=1, ge=1, le=100)
    note: str | None = Field(default=None, max_length=500)


class Order(OrderCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(default="waiting", index=True)  # waiting -> in_progress -> done
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class OrderOut(OrderCreate):
    """What the API returns: a plain model, so the docs schema is clean."""

    id: int
    status: str
    created_at: datetime
    position: int | None = None  # place in line while waiting, 1 = next to be served


def get_session():
    with Session(engine) as session:
        yield session


def queue_position(session, order):
    if order.status != "waiting":
        return None
    ahead = session.exec(
        select(func.count()).select_from(Order).where(Order.status == "waiting", Order.id < order.id)
    ).one()
    return ahead + 1


def with_position(session, order):
    return OrderOut(**order.model_dump(), position=queue_position(session, order))


@asynccontextmanager
async def lifespan(_app):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="Food Order Queue", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.post("/api/orders", status_code=201, response_model=OrderOut)
def place_order(order: OrderCreate, session: Session = Depends(get_session)):
    db_order = Order.model_validate(order)
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return with_position(session, db_order)


@app.get("/api/orders", response_model=list[OrderOut])
def list_orders(status: str | None = None, session: Session = Depends(get_session)):
    query = select(Order).order_by(Order.id)  # ids increase with arrival: FIFO order
    if status:
        query = query.where(Order.status == status)
    return [with_position(session, order) for order in session.exec(query)]


@app.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Order not found")
    return with_position(session, order)


@app.post("/api/orders/next", response_model=OrderOut)
def serve_next(session: Session = Depends(get_session)):
    """Staff take the oldest waiting order; nobody can skip the line."""
    order = session.exec(select(Order).where(Order.status == "waiting").order_by(Order.id)).first()
    if order is None:
        raise HTTPException(404, "No waiting orders")
    order.status = "in_progress"
    session.commit()
    session.refresh(order)
    return with_position(session, order)


@app.post("/api/orders/{order_id}/done", response_model=OrderOut)
def complete_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Order not found")
    if order.status != "in_progress":
        raise HTTPException(409, f"Order is {order.status}, not in_progress")
    order.status = "done"
    session.commit()
    session.refresh(order)
    return with_position(session, order)
