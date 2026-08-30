import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from backend.app.core.database import Base


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # PAYEE, TRANSACTION, USER
    entity_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)              # REPORT_FILED, RISK_UPDATED, COOLING_REEVALUATION
    old_risk = Column(Float, nullable=False)
    new_risk = Column(Float, nullable=False)
    reason = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
