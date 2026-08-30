import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    upi_id = Column(String(100), unique=True, index=True, nullable=False)
    account_number = Column(String(50), unique=True, index=True, nullable=False)
    ifsc_code = Column(String(20), default="SIMU0001234", nullable=False)
    balance = Column(Float, default=10000.0, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    is_frozen = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="accounts")
    outgoing_transactions = relationship("Transaction", back_populates="sender_account", foreign_keys="Transaction.sender_account_id")
