import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class AuditAction(str, Enum):
    LOGIN = "LOGIN"
    TRANSACTION_CREATED = "TRANSACTION_CREATED"
    RISK_ANALYZED = "RISK_ANALYZED"
    WARNING_SHOWN = "WARNING_SHOWN"
    USER_CONFIRMED = "USER_CONFIRMED"
    FUNDS_HELD = "FUNDS_HELD"
    RISK_UPDATED = "RISK_UPDATED"
    PAYMENT_RELEASED = "PAYMENT_RELEASED"
    PAYMENT_REFUNDED = "PAYMENT_REFUNDED"
    REPORT_SUBMITTED = "REPORT_SUBMITTED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)  # TRANSACTION, PAYEE, USER, REPORT
    entity_id = Column(String(100), nullable=True, index=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
