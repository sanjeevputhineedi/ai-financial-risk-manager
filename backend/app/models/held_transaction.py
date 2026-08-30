import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class HeldStatus(str, Enum):
    HELD = "HELD"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"


class HeldTransaction(Base):
    __tablename__ = "held_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    held_amount = Column(Float, nullable=False)
    cooling_period_minutes = Column(Integer, default=30, nullable=False)
    hold_expires_at = Column(DateTime, nullable=False)
    status = Column(String(50), default=HeldStatus.HELD.value, nullable=False, index=True)
    
    release_reason = Column(String(500), nullable=True)
    refund_reason = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    transaction = relationship("Transaction", back_populates="held_details")
