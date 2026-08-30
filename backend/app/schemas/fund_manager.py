from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class HeldPaymentRead(BaseModel):
    id: str
    transaction_id: str
    held_amount: float
    cooling_period_minutes: int
    hold_expires_at: datetime
    status: str
    release_reason: Optional[str] = None
    refund_reason: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReleaseRefundRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for releasing or refunding funds")


class FundManagerPoolRead(BaseModel):
    id: str
    account_number: str
    balance: float
    currency: str
    last_audit_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
