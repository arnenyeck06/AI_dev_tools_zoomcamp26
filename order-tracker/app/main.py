import logging
import os
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel, Field

from app.telemetry import LOGGER_NAME, setup_telemetry


DB_PATH = Path(os.getenv("ORDER_DB_PATH", "data/orders.db"))
STATUSES = {"received", "preparing", "shipped", "delivered"}
ORDER_ROUTE = "/api/orders/{order_id}"

setup_telemetry()
logger = logging.getLogger(LOGGER_NAME)
tracer = trace.get_tracer("order_tracker")
meter = metrics.get_meter("order_tracker")
order_lookups = meter.create_counter(
    "order_lookups",
    unit="{lookup}",
    description="Order lookups by route and HTTP status code",
)
order_lookup_duration = meter.create_histogram(
    "order_lookup_duration",
    unit="s",
    description="Order lookup duration by route and HTTP status code",
    # The SDK's default buckets are sized for milliseconds; this records seconds.
    explicit_bucket_boundaries_advisory=[0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)
# Start the 5xx series at 0. Prometheus' increase() ignores a counter's first
# sample, so without this the first 500 after a restart would not alert.
order_lookups.add(0, {"http.route": ORDER_ROUTE, "http.response.status_code": 500})


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer TEXT NOT NULL,
                item TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        if db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            now = datetime.now(timezone.utc)
            previous_month_end = now.replace(day=1) - timedelta(days=1)
            for order in (
                ("standard-1001", "Avery", "Notebook", "standard", "received", now),
                ("express-1002", "Sam", "Headphones", "express", "preparing", previous_month_end),
                ("standard-1003", "Riley", "Water bottle", "standard", "shipped", now),
            ):
                db.execute(
                    "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
                    (*order[:5], order[5].isoformat()),
                )


def as_dict(row):
    return dict(row) if row else None


def order_detail(row):
    order = as_dict(row)
    if order["priority"] == "express":
        placed_at = datetime.fromisoformat(order["created_at"])
        estimated_at = placed_at + timedelta(days=2)
        order["estimated_delivery"] = estimated_at.date().isoformat()
    return order


class NewOrder(BaseModel):
    customer: str = Field(min_length=1, max_length=80)
    item: str = Field(min_length=1, max_length=120)
    priority: str = "standard"


class StatusUpdate(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Order Tracker", lifespan=lifespan)


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent.parent / "static" / "index.html")


@app.get("/healthz")
def health():
    with connect() as db:
        db.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/api/orders")
def list_orders():
    with connect() as db:
        rows = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    return [as_dict(row) for row in rows]


def load_order(order_id: str):
    with connect() as db:
        row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Order not found")
    return order_detail(row)


@app.get(ORDER_ROUTE)
def get_order(order_id: str):
    start = time.perf_counter()
    status_code = 200
    with tracer.start_as_current_span(
        "order.lookup",
        attributes={"order.id": order_id, "http.route": ORDER_ROUTE},
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            order = load_order(order_id)
        except HTTPException as exc:
            status_code = exc.status_code
            logger.warning(
                "Order lookup failed: order_id=%s status_code=%s detail=%s",
                order_id, status_code, exc.detail,
                extra={"order.id": order_id, "http.response.status_code": status_code},
            )
            raise
        except Exception as exc:
            status_code = 500
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            logger.exception(
                "Order lookup error: order_id=%s status_code=%s",
                order_id, status_code,
                extra={"order.id": order_id, "http.response.status_code": status_code},
            )
            raise
        else:
            logger.info(
                "Order lookup succeeded: order_id=%s status_code=%s",
                order_id, status_code,
                extra={"order.id": order_id, "http.response.status_code": status_code},
            )
            return order
        finally:
            span.set_attribute("http.response.status_code", status_code)
            attributes = {"http.route": ORDER_ROUTE, "http.response.status_code": status_code}
            order_lookups.add(1, attributes)
            order_lookup_duration.record(time.perf_counter() - start, attributes)


@app.post("/api/orders", status_code=201)
def create_order(order: NewOrder):
    if order.priority not in {"standard", "express"}:
        raise HTTPException(422, "Priority must be standard or express")
    order_id = str(uuid4())
    with connect() as db:
        db.execute(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, order.customer, order.item, order.priority, "received",
             datetime.now(timezone.utc).isoformat()),
        )
    return load_order(order_id)


@app.patch("/api/orders/{order_id}")
def update_status(order_id: str, update: StatusUpdate):
    if update.status not in STATUSES:
        raise HTTPException(422, "Invalid status")
    with connect() as db:
        cursor = db.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (update.status, order_id),
        )
    if cursor.rowcount == 0:
        raise HTTPException(404, "Order not found")
    return load_order(order_id)
