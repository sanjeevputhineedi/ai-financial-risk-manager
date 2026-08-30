from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RiskAnalysisRequest(BaseModel):
    sender_id: str = Field(..., description="ID or account of sender")
    recipient_id: str = Field(..., description="VPA or ID of recipient")
    amount: float = Field(..., gt=0.0, description="Amount in INR")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional transaction/device/user context")


class RiskAnalysisResponse(BaseModel):
    personal_risk: float = Field(..., ge=0.0, le=100.0, description="Personal behavioral risk score")
    payee_risk: float = Field(..., ge=0.0, le=100.0, description="Payee reputation / scam risk score")
    overall_risk: float = Field(..., ge=0.0, le=100.0, description="Combined financial risk score")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    decision: str = Field(..., description="ALLOW, WARN, HOLD, BLOCK")
    requires_confirmation: bool = Field(..., description="True if user confirmation warning required")
    requires_hold: bool = Field(..., description="True if cooling period escrow hold required")
    reasons: List[str] = Field(default_factory=list, description="Human-understandable explanations for risk")
    model_version: Optional[str] = "payee-v1+personal-v1"


class RiskScoreRead(BaseModel):
    id: str
    transaction_id: str
    personal_risk: float
    payee_risk: float
    overall_risk: float
    risk_level: str
    confidence: float
    reasons: List[str]
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
