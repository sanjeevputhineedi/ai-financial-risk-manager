from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.held_transaction import HeldTransaction, HeldStatus
from backend.app.models.transaction import Transaction
from backend.app.models.payee_reputation import PayeeReputation
from backend.app.models.risk_event import RiskEvent
from backend.app.repositories.held_payment_repo import HeldPaymentRepository
from backend.app.repositories.transaction_repo import TransactionRepository
from backend.app.repositories.payee_repo import PayeeRepository
from backend.app.services.fund_manager_service import FundManagerService


class DynamicCoolingService:
    def __init__(self, db: Session):
        self.db = db
        self.held_repo = HeldPaymentRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.payee_repo = PayeeRepository(db)
        self.fund_manager_service = FundManagerService(db)

    def reevaluate_held_transactions(self) -> List[Dict[str, Any]]:
        """
        Dynamic Cooling Logic (Checkpoint M8):
        Scans all active HELD transactions and re-evaluates risk.
        - If recipient risk <= RELEASE_RISK_THRESHOLD -> auto release
        - If recipient risk >= REFUND_RISK_THRESHOLD  -> auto refund
        - If hold expired and risk safe                -> auto release
        """
        active_held = self.held_repo.get_active_held()
        results = []
        now = datetime.now(timezone.utc)

        for held in active_held:
            tx = self.tx_repo.get(held.transaction_id)
            if not tx:
                continue

            payee_rep = self.payee_repo.get_by_vpa(tx.recipient_vpa)
            current_payee_risk = payee_rep.risk_score if payee_rep else 30.0

            action_taken = None
            reason = ""

            # Check if risk escalated
            if current_payee_risk >= settings.REFUND_RISK_THRESHOLD:
                action_taken = "REFUNDED"
                reason = f"Dynamic Cooling: Payee risk escalated to {current_payee_risk:.1f} (>= threshold {settings.REFUND_RISK_THRESHOLD}). Funds protected and returned."
                self.fund_manager_service.refund_funds(held.id, reason=reason)
                
                # Log risk event
                self.payee_repo.add_risk_event(RiskEvent(
                    entity_type="TRANSACTION",
                    entity_id=tx.id,
                    event_type="COOLING_SCAM_ESCALATION",
                    old_risk=tx.payee_risk_score or 0.0,
                    new_risk=current_payee_risk,
                    reason=reason
                ))

            # Check if risk decayed / false positive cleared
            elif current_payee_risk <= settings.RELEASE_RISK_THRESHOLD:
                action_taken = "RELEASED"
                reason = f"Dynamic Cooling: Payee risk normalized to {current_payee_risk:.1f} (<= threshold {settings.RELEASE_RISK_THRESHOLD}). Funds released."
                self.fund_manager_service.release_funds(held.id, reason=reason)
                
                # Log risk event
                self.payee_repo.add_risk_event(RiskEvent(
                    entity_type="TRANSACTION",
                    entity_id=tx.id,
                    event_type="COOLING_FALSE_POSITIVE_RESOLVED",
                    old_risk=tx.payee_risk_score or 0.0,
                    new_risk=current_payee_risk,
                    reason=reason
                ))

            # Check if cooling period timer expired
            elif held.hold_expires_at <= now:
                if current_payee_risk < 60.0:
                    action_taken = "RELEASED"
                    reason = "Cooling period elapsed without risk escalation. Funds released to recipient."
                    self.fund_manager_service.release_funds(held.id, reason=reason)
                else:
                    action_taken = "REFUNDED"
                    reason = "Cooling period elapsed and recipient risk remained elevated. Funds safely refunded to sender."
                    self.fund_manager_service.refund_funds(held.id, reason=reason)

            if action_taken:
                results.append({
                    "held_id": held.id,
                    "transaction_id": tx.id,
                    "action": action_taken,
                    "payee_risk": current_payee_risk,
                    "reason": reason
                })

        return results
