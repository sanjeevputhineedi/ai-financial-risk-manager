from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.core.errors import NotFoundError, InsufficientBalanceError
from backend.app.models.account import Account
from backend.app.models.recipient import Recipient
from backend.app.models.user import User
from backend.app.repositories.account_repo import AccountRepository
from backend.app.repositories.payee_repo import PayeeRepository
from backend.app.schemas.account import RecipientCreate


class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.payee_repo = PayeeRepository(db)

    def get_account_by_user(self, user_id: str) -> Account:
        account = self.account_repo.get_by_user_id(user_id)
        if not account:
            raise NotFoundError("Account not found for current user")
        return account

    def get_account_by_upi_id(self, upi_id: str) -> Optional[Account]:
        return self.account_repo.get_by_upi_id(upi_id)

    def get_recipients(self, user_id: str) -> List[Recipient]:
        return self.account_repo.get_recipients_for_user(user_id)

    def add_recipient(self, user_id: str, req: RecipientCreate) -> Recipient:
        existing = self.account_repo.get_recipient_by_vpa(user_id, req.payee_vpa)
        if existing:
            return existing

        # Check payee reputation
        payee_rep = self.payee_repo.get_by_vpa(req.payee_vpa)
        risk_level = payee_rep.risk_level if payee_rep else "LOW"
        is_verified = True if payee_rep and payee_rep.reputation_score >= 80 else False

        recipient = Recipient(
            user_id=user_id,
            payee_vpa=req.payee_vpa,
            payee_name=req.payee_name,
            account_number=req.account_number,
            ifsc_code=req.ifsc_code,
            is_verified=is_verified,
            risk_level=risk_level
        )
        return self.account_repo.create_recipient(recipient)

    def update_balance(self, account_id: str, amount_delta: float) -> Account:
        account = self.account_repo.get(account_id)
        if not account:
            raise NotFoundError("Account not found")

        if account.balance + amount_delta < 0:
            raise InsufficientBalanceError(f"Insufficient balance. Current balance is ₹{account.balance:.2f}")

        account.balance += amount_delta
        return self.account_repo.update(account)
