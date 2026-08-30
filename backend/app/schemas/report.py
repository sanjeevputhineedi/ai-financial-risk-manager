from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FraudReportCreate(BaseModel):
    payee_vpa: str = Field(..., min_length=3, max_length=100)
    transaction_id: Optional[str] = None
    category: str = Field(..., description="SUSPECTED_FRAUD, DELIVERY_DELAY, SERVICE_DISPUTE, REFUND_DISPUTE, OTHER")
    description: str = Field(..., min_length=5, max_length=1000)


class FraudReportStatusUpdate(BaseModel):
    status: str = Field(..., description="PENDING, INVESTIGATING, VERIFIED, DISMISSED")
    notes: Optional[str] = None


class FraudReportRead(BaseModel):
    id: str
    reporter_user_id: str
    payee_vpa: str
    transaction_id: Optional[str] = None
    category: str
    description: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
