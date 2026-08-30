import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from backend.app.core.database import Base


class FundManagerAccount(Base):
    __tablename__ = "fund_manager"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    account_number = Column(String(50), unique=True, index=True, default="ESCROW_POOL_001", nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    last_audit_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
