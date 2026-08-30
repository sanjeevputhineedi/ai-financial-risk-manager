from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.payee_reputation import PayeeReputation
from backend.app.models.risk_event import RiskEvent
from backend.app.repositories.base import BaseRepository


class PayeeRepository(BaseRepository[PayeeReputation]):
    def __init__(self, db: Session):
        super().__init__(PayeeReputation, db)

    def get_by_vpa(self, payee_vpa: str) -> Optional[PayeeReputation]:
        return self.db.query(PayeeReputation).filter(PayeeReputation.payee_vpa == payee_vpa).first()

    def get_or_create(self, payee_vpa: str, payee_name: Optional[str] = None) -> PayeeReputation:
        payee = self.get_by_vpa(payee_vpa)
        if not payee:
            payee = PayeeReputation(
                payee_vpa=payee_vpa,
                payee_name=payee_name or payee_vpa.split("@")[0].title(),
                total_transactions=0,
                successful_transactions=0,
                reported_count=0,
                reputation_score=75.0,  # neutral default for unknown payee
                risk_score=25.0,
                risk_level="LOW"
            )
            self.db.add(payee)
            self.db.commit()
            self.db.refresh(payee)
        return payee

    def add_risk_event(self, event: RiskEvent) -> RiskEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_risk_events(self, entity_type: str, entity_id: str) -> List[RiskEvent]:
        return self.db.query(RiskEvent).filter(
            RiskEvent.entity_type == entity_type,
            RiskEvent.entity_id == entity_id
        ).order_by(RiskEvent.created_at.desc()).all()
