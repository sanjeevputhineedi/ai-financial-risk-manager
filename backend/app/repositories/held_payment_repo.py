from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.held_transaction import HeldTransaction, HeldStatus
from backend.app.models.transaction import Transaction
from backend.app.repositories.base import BaseRepository


class HeldPaymentRepository(BaseRepository[HeldTransaction]):
    def __init__(self, db: Session):
        super().__init__(HeldTransaction, db)

    def get_by_transaction_id(self, transaction_id: str) -> Optional[HeldTransaction]:
        return self.db.query(HeldTransaction).filter(HeldTransaction.transaction_id == transaction_id).first()

    def get_active_held(self) -> List[HeldTransaction]:
        return self.db.query(HeldTransaction).filter(HeldTransaction.status == HeldStatus.HELD.value).all()

    def get_held_for_user_transactions(self, user_account_id: str) -> List[HeldTransaction]:
        return self.db.query(HeldTransaction).join(
            Transaction, HeldTransaction.transaction_id == Transaction.id
        ).filter(Transaction.sender_account_id == user_account_id).all()
