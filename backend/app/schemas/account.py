from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AccountRead(BaseModel):
    id: str
    user_id: str
    upi_id: str
    account_number: str
    ifsc_code: str
    balance: float
    currency: str
    is_frozen: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountBalanceUpdate(BaseModel):
    amount: float = Field(..., description="Amount to deposit/credit or withdraw/debit")


class RecipientCreate(BaseModel):
    payee_vpa: str = Field(..., min_length=3, max_length=100)
    payee_name: str = Field(..., min_length=1, max_length=255)
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None


class RecipientRead(BaseModel):
    id: str
    user_id: str
    payee_vpa: str
    payee_name: str
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    is_verified: bool
    risk_level: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
