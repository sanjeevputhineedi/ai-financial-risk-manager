from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.account import Account
from backend.app.models.recipient import Recipient
from backend.app.models.fund_manager import FundManagerAccount
from backend.app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, db: Session):
        super().__init__(Account, db)

    def get_by_user_id(self, user_id: str) -> Optional[Account]:
        return self.db.query(Account).filter(Account.user_id == user_id).first()

    def get_by_upi_id(self, upi_id: str) -> Optional[Account]:
        return self.db.query(Account).filter(Account.upi_id == upi_id).first()

    def get_recipients_for_user(self, user_id: str) -> List[Recipient]:
        return self.db.query(Recipient).filter(Recipient.user_id == user_id).all()

    def get_recipient_by_vpa(self, user_id: str, payee_vpa: str) -> Optional[Recipient]:
        return self.db.query(Recipient).filter(
            Recipient.user_id == user_id,
            Recipient.payee_vpa == payee_vpa
        ).first()

    def create_recipient(self, recipient: Recipient) -> Recipient:
        self.db.add(recipient)
        self.db.commit()
        self.db.refresh(recipient)
        return recipient

    def get_fund_manager_account(self) -> FundManagerAccount:
        escrow = self.db.query(FundManagerAccount).first()
        if not escrow:
            escrow = FundManagerAccount(
                account_number="ESCROW_POOL_001",
                balance=0.0,
                currency="INR"
            )
            self.db.add(escrow)
            self.db.commit()
            self.db.refresh(escrow)
        return escrow
