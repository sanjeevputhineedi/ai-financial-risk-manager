from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class RiskBreakdown(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class HeldPaymentsSummary(BaseModel):
    currently_held: int
    released: int
    refunded: int
    total_held_volume: float
    total_refunded_volume: float


class DashboardMetricsResponse(BaseModel):
    total_transactions: int
    risk_distribution: RiskBreakdown
    held_summary: HeldPaymentsSummary
    fraud_reports_count: int
    average_personal_risk: float
    average_payee_risk: float
    suspicious_recipients_count: int
    false_positives_mitigated: int
    federated_rounds_completed: int
    active_federated_clients: int
    escrow_pool_balance: float
