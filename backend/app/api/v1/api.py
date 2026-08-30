from fastapi import APIRouter
from backend.app.api.v1 import (
    auth,
    users,
    accounts,
    transactions,
    risk,
    payees,
    reports,
    held_payments,
    audit,
    dashboard
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(accounts.recipients_router, prefix="/recipients", tags=["Recipients"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk ML Integration"])
api_router.include_router(payees.router, prefix="/payees", tags=["Payee Reputation"])
api_router.include_router(reports.router, prefix="/reports", tags=["Fraud Reports"])
api_router.include_router(held_payments.router, prefix="/held-payments", tags=["Fund Manager & Escrow"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit System"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard Metrics"])
