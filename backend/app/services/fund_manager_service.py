from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.errors import (
    NotFoundError,
    HeldPaymentActionError,
    InsufficientBalanceError,
    InvalidStateTransitionError
)
from backend.app.models.transaction import Transaction, TransactionStatus
from backend.app.models.held_transaction import HeldTransaction, HeldStatus
from backend.app.models.fund_manager import FundManagerAccount
from backend.app.models.account import Account
from backend.app.models.audit_log import AuditAction
from backend.app.repositories.transaction_repo import TransactionRepository
from backend.app.repositories.held_payment_repo import HeldPaymentRepository
from backend.app.repositories.account_repo import AccountRepository
from backend.app.repositories.audit_repo import AuditRepository


class FundManagerService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = TransactionRepository(db)
        self.held_repo = HeldPaymentRepository(db)
        self.account_repo = AccountRepository(db)
        self.audit_repo = AuditRepository(db)

    def hold_transaction_funds(
        self,
        transaction: Transaction,
        cooling_period_minutes: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> HeldTransaction:
        """
        Escrow Hold: Debits sender, credits Fund Manager Escrow pool, keeps recipient at 0 credit.
        """
        if transaction.status not in [TransactionStatus.CONFIRMED.value, TransactionStatus.ANALYZING.value, TransactionStatus.INITIATED.value]:
            raise InvalidStateTransitionError(f"Cannot hold transaction with status {transaction.status}")

        sender_account = self.account_repo.get(transaction.sender_account_id)
        if not sender_account:
            raise NotFoundError("Sender account not found")

        if sender_account.balance < transaction.amount:
            raise InsufficientBalanceError(f"Insufficient funds to hold ₹{transaction.amount:.2f}")

        # Debit sender
        sender_account.balance -= transaction.amount

        # Credit Fund Manager escrow pool
        escrow = self.account_repo.get_fund_manager_account()
        escrow.balance += transaction.amount
        escrow.last_audit_at = datetime.now(timezone.utc)

        # Set cooling period
        minutes = cooling_period_minutes or settings.COOLING_PERIOD_MINUTES
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)

        held_tx = HeldTransaction(
            transaction_id=transaction.id,
            held_amount=transaction.amount,
            cooling_period_minutes=minutes,
            hold_expires_at=expires_at,
            status=HeldStatus.HELD.value
        )
        self.db.add(held_tx)

        transaction.status = TransactionStatus.HELD.value
        transaction.updated_at = datetime.now(timezone.utc)

        # Audit log
        self.audit_repo.log(
            action=AuditAction.FUNDS_HELD.value,
            user_id=sender_account.user_id,
            entity_type="TRANSACTION",
            entity_id=transaction.id,
            details={
                "amount": transaction.amount,
                "cooling_period_minutes": minutes,
                "hold_expires_at": expires_at.isoformat(),
                "escrow_pool_balance": escrow.balance
            },
            ip_address=ip_address
        )

        self.db.commit()
        self.db.refresh(held_tx)
        return held_tx

    def release_funds(
        self,
        held_id: str,
        reason: str,
        admin_user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> HeldTransaction:
        """
        Release Escrow: Debits Fund Manager Escrow pool, credits Recipient account (if in system).
        """
        held_tx = self.held_repo.get(held_id)
        if not held_tx:
            raise NotFoundError(f"Held payment record {held_id} not found")

        if held_tx.status != HeldStatus.HELD.value:
            raise HeldPaymentActionError(f"Payment is already {held_tx.status}. Cannot release.")

        transaction = self.transaction_repo.get(held_tx.transaction_id)
        if not transaction:
            raise NotFoundError("Associated transaction not found")

        escrow = self.account_repo.get_fund_manager_account()
        if escrow.balance < held_tx.held_amount:
            raise InsufficientBalanceError("Fund Manager pool balance error during release")

        # Debit escrow pool
        escrow.balance -= held_tx.held_amount
        escrow.last_audit_at = datetime.now(timezone.utc)

        # Credit recipient if recipient account exists in simulated system
        recipient_acc = self.account_repo.get_by_upi_id(transaction.recipient_vpa)
        if recipient_acc:
            recipient_acc.balance += held_tx.held_amount

        held_tx.status = HeldStatus.RELEASED.value
        held_tx.release_reason = reason
        held_tx.resolved_at = datetime.now(timezone.utc)

        transaction.status = TransactionStatus.RELEASED.value
        transaction.updated_at = datetime.now(timezone.utc)

        # Audit log
        self.audit_repo.log(
            action=AuditAction.PAYMENT_RELEASED.value,
            user_id=admin_user_id,
            entity_type="TRANSACTION",
            entity_id=transaction.id,
            details={
                "held_id": held_id,
                "amount": held_tx.held_amount,
                "reason": reason,
                "recipient_vpa": transaction.recipient_vpa
            },
            ip_address=ip_address
        )

        self.db.commit()
        self.db.refresh(held_tx)
        return held_tx

    def refund_funds(
        self,
        held_id: str,
        reason: str,
        admin_user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> HeldTransaction:
        """
        Refund Escrow: Debits Fund Manager Escrow pool, refunds Sender account.
        """
        held_tx = self.held_repo.get(held_id)
        if not held_tx:
            raise NotFoundError(f"Held payment record {held_id} not found")

        if held_tx.status != HeldStatus.HELD.value:
            raise HeldPaymentActionError(f"Payment is already {held_tx.status}. Cannot refund.")

        transaction = self.transaction_repo.get(held_tx.transaction_id)
        if not transaction:
            raise NotFoundError("Associated transaction not found")

        escrow = self.account_repo.get_fund_manager_account()
        if escrow.balance < held_tx.held_amount:
            raise InsufficientBalanceError("Fund Manager pool balance error during refund")

        # Debit escrow pool
        escrow.balance -= held_tx.held_amount
        escrow.last_audit_at = datetime.now(timezone.utc)

        # Refund sender account
        sender_acc = self.account_repo.get(transaction.sender_account_id)
        if sender_acc:
            sender_acc.balance += held_tx.held_amount

        held_tx.status = HeldStatus.REFUNDED.value
        held_tx.refund_reason = reason
        held_tx.resolved_at = datetime.now(timezone.utc)

        transaction.status = TransactionStatus.REFUNDED.value
        transaction.updated_at = datetime.now(timezone.utc)

        # Audit log
        self.audit_repo.log(
            action=AuditAction.PAYMENT_REFUNDED.value,
            user_id=admin_user_id,
            entity_type="TRANSACTION",
            entity_id=transaction.id,
            details={
                "held_id": held_id,
                "amount": held_tx.held_amount,
                "reason": reason,
                "refunded_to": sender_acc.upi_id if sender_acc else "sender"
            },
            ip_address=ip_address
        )

        self.db.commit()
        self.db.refresh(held_tx)
        return held_tx

    def list_held_payments(self, skip: int = 0, limit: int = 50) -> List[HeldTransaction]:
        return self.held_repo.get_all(skip=skip, limit=limit)

    def get_held_payment(self, held_id: str) -> HeldTransaction:
        held = self.held_repo.get(held_id)
        if not held:
            raise NotFoundError(f"Held payment {held_id} not found")
        return held
