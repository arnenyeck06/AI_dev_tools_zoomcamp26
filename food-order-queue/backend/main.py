"""Food order queue API: customers place orders, staff serve them first in, first out."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, func, select

import flags

# SQLite file locally; PostgreSQL in Docker Compose, e.g. postgresql+psycopg://user:pass@db:5432/orders
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///orders.db")


def make_engine(url):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


engine = make_engine(DATABASE_URL)
USUAL_WAIT_SAMPLE = 50  # served orders used to compute the usual wait


def utcnow():
    return datetime.now(timezone.utc)


def as_utc(value):
    """SQLite returns naive datetimes; every time we store is UTC."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class OrderCreate(SQLModel):
    customer_name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=7, max_length=20)
    item: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=1, ge=1, le=100)
    note: str | None = Field(default=None, max_length=500)


class Order(OrderCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(default="waiting", index=True)  # waiting -> in_progress -> done
    created_at: datetime = Field(default_factory=lambda: utcnow(), index=True)
    served_at: datetime | None = None


class Flag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", index=True)
    source: str  # rule or ai
    reason: str
    severity: str  # low, medium, high
    created_at: datetime = Field(default_factory=lambda: utcnow())


class FlagOut(SQLModel):
    source: str
    reason: str
    severity: str


class OrderOut(OrderCreate):
    """What the API returns: a plain model, so the docs schema is clean."""

    id: int
    status: str
    created_at: datetime
    position: int | None = None  # place in line while waiting, 1 = next to be served
    flags: list[FlagOut] = []


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


def usual_waits(session):
    """How long recently served orders waited."""
    served = session.exec(
        select(Order).where(Order.served_at != None).order_by(Order.id.desc()).limit(USUAL_WAIT_SAMPLE)  # noqa: E711
    )
    return [as_utc(o.served_at) - as_utc(o.created_at) for o in served]


def order_flags(session, order, waits):
    """Saved flags, plus a long-wait flag worked out now for orders still waiting."""
    saved = session.exec(select(Flag).where(Flag.order_id == order.id).order_by(Flag.id))
    result = [FlagOut(source=f.source, reason=f.reason, severity=f.severity) for f in saved]
    if order.status == "waiting":
        long_wait = flags.long_wait_flag(utcnow() - as_utc(order.created_at), waits)
        if long_wait:
            result.append(FlagOut(source="rule", reason=long_wait[0], severity=long_wait[1]))
    return result


def to_out(session, order, waits=None):
    if waits is None:
        waits = usual_waits(session)
    return OrderOut(
        **order.model_dump(exclude={"served_at"}),
        position=queue_position(session, order),
        flags=order_flags(session, order, waits),
    )


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
    db_order = Order.model_validate(order, update={"created_at": utcnow()})
    earlier = session.exec(
        select(Order.item, Order.created_at).where(
            Order.phone == db_order.phone, Order.created_at >= db_order.created_at - flags.BURST_WINDOW
        )
    ).all()
    session.add(db_order)
    session.flush()  # assigns the id the flags point to
    found = flags.placement_flags(
        db_order.quantity, db_order.item, db_order.created_at, [(item, as_utc(at)) for item, at in earlier]
    )
    for reason, severity in found:
        session.add(Flag(order_id=db_order.id, source="rule", reason=reason, severity=severity))
    session.commit()  # flags never reject an order or change its place in line
    session.refresh(db_order)
    return to_out(session, db_order)


@app.get("/api/orders", response_model=list[OrderOut])
def list_orders(status: str | None = None, session: Session = Depends(get_session)):
    query = select(Order).order_by(Order.id)  # ids increase with arrival: FIFO order
    if status:
        query = query.where(Order.status == status)
    waits = usual_waits(session)
    return [to_out(session, order, waits) for order in session.exec(query)]


@app.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Order not found")
    return to_out(session, order)


@app.post("/api/orders/next", response_model=OrderOut)
def serve_next(session: Session = Depends(get_session)):
    """Staff take the oldest waiting order; nobody can skip the line."""
    # FOR UPDATE SKIP LOCKED: two staff pressing at once on PostgreSQL get different orders (SQLite ignores it)
    order = session.exec(
        select(Order).where(Order.status == "waiting").order_by(Order.id).limit(1).with_for_update(skip_locked=True)
    ).first()
    if order is None:
        raise HTTPException(404, "No waiting orders")
    order.status = "in_progress"
    order.served_at = utcnow()
    session.commit()
    session.refresh(order)
    return to_out(session, order)


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
    return to_out(session, order)
