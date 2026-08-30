from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.core.errors import (
    NotFoundError,
    InsufficientBalanceError,
    InvalidStateTransitionError,
    DuplicateIdempotencyError,
    AppException
)
from backend.app.models.transaction import Transaction, TransactionStatus
from backend.app.models.risk_score import RiskScore
from backend.app.models.audit_log import AuditAction
from backend.app.repositories.transaction_repo import TransactionRepository
from backend.app.repositories.account_repo import AccountRepository
from backend.app.repositories.payee_repo import PayeeRepository
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.schemas.transaction import TransactionCreate, TransactionConfirmRequest
from backend.app.schemas.risk import RiskAnalysisRequest
from backend.app.services.risk_service import RiskService
from backend.app.services.fund_manager_service import FundManagerService
from backend.app.services.reputation_service import ReputationService


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.tx_repo = TransactionRepository(db)
        self.account_repo = AccountRepository(db)
        self.payee_repo = PayeeRepository(db)
        self.audit_repo = AuditRepository(db)
        self.risk_service = RiskService(db)
        self.fund_manager_service = FundManagerService(db)
        self.reputation_service = ReputationService(db)

    def create_transaction(
        self,
        sender_user_id: str,
        req: TransactionCreate,
        ip_address: Optional[str] = None
    ) -> Transaction:
        # Check idempotency
        if req.idempotency_key:
            existing = self.tx_repo.get_by_idempotency_key(req.idempotency_key)
            if existing:
                return existing

        sender_account = self.account_repo.get_by_user_id(sender_user_id)
        if not sender_account:
            raise NotFoundError("Sender account not found for user")

        if sender_account.is_frozen:
            raise AppException("Account is frozen. Cannot initiate transactions.", status_code=403)

        if sender_account.balance < req.amount:
            raise InsufficientBalanceError(
                f"Insufficient balance. Available: ₹{sender_account.balance:.2f}, Required: ₹{req.amount:.2f}"
            )

        # Get recipient name
        recipient_name = req.recipient_name
        if not recipient_name:
            payee_rep = self.payee_repo.get_by_vpa(req.recipient_vpa)
            recipient_name = payee_rep.payee_name if payee_rep and payee_rep.payee_name else req.recipient_vpa.split("@")[0].title()

        # Step 1: Initialize transaction
        tx = Transaction(
            idempotency_key=req.idempotency_key,
            sender_account_id=sender_account.id,
            recipient_vpa=req.recipient_vpa,
            recipient_name=recipient_name,
            amount=req.amount,
            status=TransactionStatus.INITIATED.value,
            notes=req.notes
        )
        self.db.add(tx)
        self.db.flush()

        # Step 2: Risk Analysis (M5 Integration Contract)
        tx.status = TransactionStatus.ANALYZING.value
        risk_res = self.risk_service.analyze_transaction(
            RiskAnalysisRequest(
                sender_id=sender_account.upi_id,
                recipient_id=req.recipient_vpa,
                amount=req.amount,
                context={"notes": req.notes, "sender_user_id": sender_user_id}
            )
        )

        tx.personal_risk_score = risk_res.personal_risk
        tx.payee_risk_score = risk_res.payee_risk
        tx.overall_risk_score = risk_res.overall_risk
        tx.risk_level = risk_res.risk_level
        tx.decision = risk_res.decision

        # Store detailed RiskScore record
        risk_score_entry = RiskScore(
            transaction_id=tx.id,
            personal_risk=risk_res.personal_risk,
            payee_risk=risk_res.payee_risk,
            overall_risk=risk_res.overall_risk,
            risk_level=risk_res.risk_level,
            confidence=0.95,
            reasons=risk_res.reasons,
            model_version=risk_res.model_version or "payee-v1+personal-v1"
        )
        self.tx_repo.save_risk_score(risk_score_entry)

        # Audit log risk analysis
        self.audit_repo.log(
            action=AuditAction.RISK_ANALYZED.value,
            user_id=sender_user_id,
            entity_type="TRANSACTION",
            entity_id=tx.id,
            details={
                "personal_risk": risk_res.personal_risk,
                "payee_risk": risk_res.payee_risk,
                "overall_risk": risk_res.overall_risk,
                "decision": risk_res.decision,
                "risk_level": risk_res.risk_level
            },
            ip_address=ip_address
        )

        # Step 3: Decision Engine Routing
        if risk_res.decision == "ALLOW":
            # Instant low-risk payment
            self._execute_instant_payment(tx, sender_account, req.recipient_vpa, req.amount, sender_user_id, ip_address)
        
        elif req.bypass_risk_warning:
            # User already confirmed in request
            self.audit_repo.log(
                action=AuditAction.USER_CONFIRMED.value,
                user_id=sender_user_id,
                entity_type="TRANSACTION",
                entity_id=tx.id,
                details={"bypass_warning": True, "decision": risk_res.decision},
                ip_address=ip_address
            )
            if risk_res.requires_hold:
                self.fund_manager_service.hold_transaction_funds(tx, ip_address=ip_address)
            else:
                self._execute_instant_payment(tx, sender_account, req.recipient_vpa, req.amount, sender_user_id, ip_address)
        
        else:
            # Requires explicit confirmation
            tx.status = TransactionStatus.CONFIRMATION_REQUIRED.value
            self.audit_repo.log(
                action=AuditAction.WARNING_SHOWN.value,
                user_id=sender_user_id,
                entity_type="TRANSACTION",
                entity_id=tx.id,
                details={"risk_level": risk_res.risk_level, "reasons": risk_res.reasons},
                ip_address=ip_address
            )
            self.db.commit()

        self.db.refresh(tx)
        return tx

    def _execute_instant_payment(
        self,
        tx: Transaction,
        sender_account,
        recipient_vpa: str,
        amount: float,
        user_id: str,
        ip_address: Optional[str] = None
    ):
        # Debit sender
        sender_account.balance -= amount

        # Credit recipient if simulated account exists
        recipient_acc = self.account_repo.get_by_upi_id(recipient_vpa)
        if recipient_acc:
            recipient_acc.balance += amount

        tx.status = TransactionStatus.COMPLETED.value
        tx.updated_at = datetime.now(timezone.utc)

        # Update reputation for successful transaction
        self.reputation_service.record_successful_transaction(recipient_vpa)

        # Audit log
        self.audit_repo.log(
            action=AuditAction.TRANSACTION_CREATED.value,
            user_id=user_id,
            entity_type="TRANSACTION",
            entity_id=tx.id,
            details={"amount": amount, "recipient_vpa": recipient_vpa, "status": "COMPLETED"},
            ip_address=ip_address
        )
        self.db.commit()

    def confirm_transaction(
        self,
        transaction_id: str,
        user_id: str,
        req: TransactionConfirmRequest,
        ip_address: Optional[str] = None
    ) -> Transaction:
        tx = self.tx_repo.get(transaction_id)
        if not tx:
            raise NotFoundError("Transaction not found")

        sender_acc = self.account_repo.get(tx.sender_account_id)
        if sender_acc.user_id != user_id:
            raise AppException("Unauthorized to confirm this transaction", status_code=403)

        if tx.status != TransactionStatus.CONFIRMATION_REQUIRED.value:
            raise InvalidStateTransitionError(f"Cannot confirm transaction with status {tx.status}")

        self.audit_repo.log(
            action=AuditAction.USER_CONFIRMED.value,
            user_id=user_id,
            entity_type="TRANSACTION",
            entity_id=tx.id,
            details={"confirmed": req.confirmed, "user_notes": req.user_notes},
            ip_address=ip_address
        )

        # Route based on decision
        if tx.decision in ["HOLD", "BLOCK"] or (tx.overall_risk_score and tx.overall_risk_score >= 70.0):
            self.fund_manager_service.hold_transaction_funds(tx, ip_address=ip_address)
        else:
            self._execute_instant_payment(tx, sender_acc, tx.recipient_vpa, tx.amount, user_id, ip_address)

        self.db.refresh(tx)
        return tx

    def cancel_transaction(
        self,
        transaction_id: str,
        user_id: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Transaction:
        tx = self.tx_repo.get(transaction_id)
        if not tx:
            raise NotFoundError("Transaction not found")

        sender_acc = self.account_repo.get(tx.sender_account_id)
        if sender_acc.user_id != user_id:
            raise AppException("Unauthorized to cancel this transaction", status_code=403)

        if tx.status not in [TransactionStatus.INITIATED.value, TransactionStatus.CONFIRMATION_REQUIRED.value, TransactionStatus.ANALYZING.value]:
            raise InvalidStateTransitionError(f"Cannot cancel transaction with status {tx.status}")

        tx.status = TransactionStatus.CANCELLED.value
        tx.notes = f"{tx.notes or ''} | Cancelled: {reason or 'User aborted'}".strip(" |")
        tx.updated_at = datetime.now(timezone.utc)

        self.audit_repo.log(
            action="TRANSACTION_CANCELLED",
            user_id=user_id,
            entity_type="TRANSACTION",
            entity_id=tx.id,
            details={"reason": reason},
            ip_address=ip_address
        )
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def list_transactions_for_user(self, user_id: str, limit: int = 50) -> List[Transaction]:
        sender_acc = self.account_repo.get_by_user_id(user_id)
        if not sender_acc:
            return []
        return self.tx_repo.get_by_sender_account(sender_acc.id, limit=limit)

    def get_transaction_by_id(self, transaction_id: str) -> Transaction:
        tx = self.tx_repo.get(transaction_id)
        if not tx:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        return tx
