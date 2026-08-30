import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    personal_risk = Column(Float, nullable=False)
    payee_risk = Column(Float, nullable=False)
    overall_risk = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, default=0.95, nullable=False)
    reasons = Column(JSON, default=list, nullable=False)
    model_version = Column(String(50), default="payee-v1", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transaction = relationship("Transaction", back_populates="risk_scores")
