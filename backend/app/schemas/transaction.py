from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TransactionCreate(BaseModel):
    recipient_vpa: str = Field(..., min_length=3, max_length=100)
    recipient_name: Optional[str] = None
    amount: float = Field(..., gt=0.0, description="Transaction amount in INR")
    notes: Optional[str] = Field(None, max_length=500)
    idempotency_key: Optional[str] = Field(None, max_length=100)
    bypass_risk_warning: Optional[bool] = Field(False, description="Explicit user confirmation for medium/high risk")


class TransactionConfirmRequest(BaseModel):
    confirmed: bool = True
    user_notes: Optional[str] = None


class TransactionCancelRequest(BaseModel):
    reason: Optional[str] = "User requested cancellation"


class TransactionRead(BaseModel):
    id: str
    idempotency_key: Optional[str] = None
    sender_account_id: str
    recipient_vpa: str
    recipient_name: str
    amount: float
    status: str
    personal_risk_score: Optional[float] = None
    payee_risk_score: Optional[float] = None
    overall_risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    decision: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
