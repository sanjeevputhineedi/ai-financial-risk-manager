from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.transaction import Transaction, TransactionStatus
from backend.app.models.held_transaction import HeldTransaction, HeldStatus
from backend.app.models.fraud_report import FraudReport
from backend.app.models.payee_reputation import PayeeReputation
from backend.app.models.federated import FederatedRound, FederatedClient
from backend.app.models.fund_manager import FundManagerAccount
from backend.app.schemas.dashboard import (
    DashboardMetricsResponse,
    RiskBreakdown,
    HeldPaymentsSummary
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_metrics(self) -> DashboardMetricsResponse:
        total_tx = self.db.query(Transaction).count()

        # Risk distribution
        low_count = self.db.query(Transaction).filter(Transaction.risk_level == "LOW").count()
        med_count = self.db.query(Transaction).filter(Transaction.risk_level == "MEDIUM").count()
        high_count = self.db.query(Transaction).filter(Transaction.risk_level == "HIGH").count()
        crit_count = self.db.query(Transaction).filter(Transaction.risk_level == "CRITICAL").count()

        # Held payments summary
        held_count = self.db.query(HeldTransaction).filter(HeldTransaction.status == HeldStatus.HELD.value).count()
        rel_count = self.db.query(HeldTransaction).filter(HeldTransaction.status == HeldStatus.RELEASED.value).count()
        ref_count = self.db.query(HeldTransaction).filter(HeldTransaction.status == HeldStatus.REFUNDED.value).count()

        held_vol = self.db.query(func.sum(HeldTransaction.held_amount)).filter(
            HeldTransaction.status == HeldStatus.HELD.value
        ).scalar() or 0.0

        ref_vol = self.db.query(func.sum(HeldTransaction.held_amount)).filter(
            HeldTransaction.status == HeldStatus.REFUNDED.value
        ).scalar() or 0.0

        # Reports & Payees
        reports_count = self.db.query(FraudReport).count()
        suspicious_payees = self.db.query(PayeeReputation).filter(PayeeReputation.risk_score >= 70.0).count()

        # Averages
        avg_personal = self.db.query(func.avg(Transaction.personal_risk_score)).filter(
            Transaction.personal_risk_score.isnot(None)
        ).scalar() or 18.5

        avg_payee = self.db.query(func.avg(Transaction.payee_risk_score)).filter(
            Transaction.payee_risk_score.isnot(None)
        ).scalar() or 22.0

        # Escrow pool balance
        escrow = self.db.query(FundManagerAccount).first()
        escrow_balance = escrow.balance if escrow else 0.0

        # Federated Learning stats
        fl_rounds = self.db.query(FederatedRound).count()
        fl_clients = self.db.query(FederatedClient).filter(FederatedClient.status == "ONLINE").count()

        # False positives mitigated = payments that were held and later safely released
        false_positives = rel_count

        return DashboardMetricsResponse(
            total_transactions=total_tx,
            risk_distribution=RiskBreakdown(
                low=low_count,
                medium=med_count,
                high=high_count,
                critical=crit_count
            ),
            held_summary=HeldPaymentsSummary(
                currently_held=held_count,
                released=rel_count,
                refunded=ref_count,
                total_held_volume=round(held_vol, 2),
                total_refunded_volume=round(ref_vol, 2)
            ),
            fraud_reports_count=reports_count,
            average_personal_risk=round(avg_personal, 1),
            average_payee_risk=round(avg_payee, 1),
            suspicious_recipients_count=suspicious_payees,
            false_positives_mitigated=false_positives,
            federated_rounds_completed=fl_rounds,
            active_federated_clients=fl_clients,
            escrow_pool_balance=round(escrow_balance, 2)
        )
