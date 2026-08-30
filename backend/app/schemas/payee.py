from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class PayeeRiskResponse(BaseModel):
    payee_vpa: str
    payee_name: Optional[str] = None
    payee_risk_score: float
    risk_level: str
    confidence: float
    reasons: List[str]
    model_version: str


class PayeeReputationResponse(BaseModel):
    id: str
    payee_vpa: str
    payee_name: Optional[str] = None
    total_transactions: int
    successful_transactions: int
    reported_count: int
    reputation_score: float
    risk_score: float
    risk_level: str
    last_evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayeeReputationUpdate(BaseModel):
    delta: Optional[float] = None
    successful: Optional[bool] = None
    reason: Optional[str] = None
