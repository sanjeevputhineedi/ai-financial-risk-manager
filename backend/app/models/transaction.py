import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class TransactionStatus(str, Enum):
    INITIATED = "INITIATED"
    ANALYZING = "ANALYZING"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    HELD = "HELD"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=True)
    sender_account_id = Column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_vpa = Column(String(100), index=True, nullable=False)
    recipient_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default=TransactionStatus.INITIATED.value, nullable=False, index=True)
    
    personal_risk_score = Column(Float, nullable=True)
    payee_risk_score = Column(Float, nullable=True)
    overall_risk_score = Column(Float, nullable=True)
    risk_level = Column(String(50), nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    decision = Column(String(50), nullable=True)    # ALLOW, WARN, HOLD, BLOCK
    
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    sender_account = relationship("Account", back_populates="outgoing_transactions", foreign_keys=[sender_account_id])
    risk_scores = relationship("RiskScore", back_populates="transaction", cascade="all, delete-orphan")
    held_details = relationship("HeldTransaction", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
