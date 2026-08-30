import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime
from backend.app.core.database import Base


class PayeeReputation(Base):
    __tablename__ = "payee_reputation"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    payee_vpa = Column(String(100), unique=True, index=True, nullable=False)
    payee_name = Column(String(255), nullable=True)
    total_transactions = Column(Integer, default=0, nullable=False)
    successful_transactions = Column(Integer, default=0, nullable=False)
    reported_count = Column(Integer, default=0, nullable=False)
    reputation_score = Column(Float, default=100.0, nullable=False)  # 0 to 100
    risk_score = Column(Float, default=10.0, nullable=False)        # 0 to 100
    risk_level = Column(String(50), default="LOW", nullable=False)
    last_evaluated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
