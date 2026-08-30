import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payee_vpa = Column(String(100), index=True, nullable=False)
    payee_name = Column(String(255), nullable=False)
    account_number = Column(String(50), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    risk_level = Column(String(50), default="LOW", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="recipients")
