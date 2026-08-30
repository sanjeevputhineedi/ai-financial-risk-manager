from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.transaction import Transaction
from backend.app.models.risk_score import RiskScore
from backend.app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: Session):
        super().__init__(Transaction, db)

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[Transaction]:
        if not idempotency_key:
            return None
        return self.db.query(Transaction).filter(Transaction.idempotency_key == idempotency_key).first()

    def get_by_sender_account(self, account_id: str, limit: int = 50) -> List[Transaction]:
        return self.db.query(Transaction).filter(
            Transaction.sender_account_id == account_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()

    def save_risk_score(self, risk_score: RiskScore) -> RiskScore:
        self.db.add(risk_score)
        self.db.commit()
        self.db.refresh(risk_score)
        return risk_score

    def get_risk_score_by_transaction_id(self, transaction_id: str) -> Optional[RiskScore]:
        return self.db.query(RiskScore).filter(RiskScore.transaction_id == transaction_id).first()
