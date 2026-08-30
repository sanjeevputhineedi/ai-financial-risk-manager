import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from backend.app.core.database import Base


class FederatedClient(Base):
    __tablename__ = "federated_clients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    client_id = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(String(50), default="ONLINE", nullable=False)  # ONLINE, OFFLINE, TRAINING
    last_round = Column(Integer, default=0, nullable=False)
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class FederatedRound(Base):
    __tablename__ = "federated_rounds"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    round_number = Column(Integer, unique=True, index=True, nullable=False)
    client_count = Column(Integer, default=0, nullable=False)
    global_loss = Column(Float, nullable=True)
    global_metrics = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
