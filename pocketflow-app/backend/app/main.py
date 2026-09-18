from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import budgets, categories, expenses, members, recurring_bills, trends

app = FastAPI(title="PocketFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(members.router)
app.include_router(expenses.router)
app.include_router(recurring_bills.router)
app.include_router(budgets.router)
app.include_router(trends.router)
