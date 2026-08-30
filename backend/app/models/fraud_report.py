import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class ReportCategory(str, Enum):
    SUSPECTED_FRAUD = "SUSPECTED_FRAUD"
    DELIVERY_DELAY = "DELIVERY_DELAY"
    SERVICE_DISPUTE = "SERVICE_DISPUTE"
    REFUND_DISPUTE = "REFUND_DISPUTE"
    OTHER = "OTHER"


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    INVESTIGATING = "INVESTIGATING"
    VERIFIED = "VERIFIED"
    DISMISSED = "DISMISSED"


class FraudReport(Base):
    __tablename__ = "fraud_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    reporter_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payee_vpa = Column(String(100), index=True, nullable=False)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), default=ReportCategory.SUSPECTED_FRAUD.value, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default=ReportStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reporter = relationship("User", back_populates="fraud_reports")
    transaction = relationship("Transaction")
