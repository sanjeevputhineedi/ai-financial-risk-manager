from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.core.errors import NotFoundError, AppException
from backend.app.models.payee_reputation import PayeeReputation
from backend.app.models.fraud_report import FraudReport, ReportCategory, ReportStatus
from backend.app.models.risk_event import RiskEvent
from backend.app.models.audit_log import AuditAction
from backend.app.repositories.payee_repo import PayeeRepository
from backend.app.repositories.report_repo import ReportRepository
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.schemas.report import FraudReportCreate
from backend.app.schemas.payee import PayeeRiskResponse, PayeeReputationResponse


class ReputationService:
    def __init__(self, db: Session):
        self.db = db
        self.payee_repo = PayeeRepository(db)
        self.report_repo = ReportRepository(db)
        self.audit_repo = AuditRepository(db)

    def get_payee_reputation(self, payee_vpa: str) -> PayeeReputationResponse:
        payee = self.payee_repo.get_or_create(payee_vpa)
        return PayeeReputationResponse.model_validate(payee)

    def create_fraud_report(
        self,
        reporter_user_id: str,
        req: FraudReportCreate,
        ip_address: Optional[str] = None
    ) -> FraudReport:
        # Validate category
        valid_cats = [c.value for c in ReportCategory]
        if req.category not in valid_cats:
            raise AppException(f"Invalid category '{req.category}'. Must be one of {valid_cats}", status_code=400)

        report = FraudReport(
            reporter_user_id=reporter_user_id,
            payee_vpa=req.payee_vpa,
            transaction_id=req.transaction_id,
            category=req.category,
            description=req.description,
            status=ReportStatus.PENDING.value
        )
        self.db.add(report)
        self.db.flush()

        # Update Payee reputation score and record risk event
        payee = self.payee_repo.get_or_create(req.payee_vpa)
        old_risk = payee.risk_score
        
        # Increase risk based on report category
        risk_increase = 15.0
        if req.category == ReportCategory.SUSPECTED_FRAUD.value:
            risk_increase = 25.0
        elif req.category == ReportCategory.REFUND_DISPUTE.value:
            risk_increase = 18.0

        payee.reported_count += 1
        payee.risk_score = min(100.0, payee.risk_score + risk_increase)
        payee.reputation_score = max(0.0, 100.0 - payee.risk_score)
        
        if payee.risk_score < 40.0:
            payee.risk_level = "LOW"
        elif payee.risk_score < 70.0:
            payee.risk_level = "MEDIUM"
        elif payee.risk_score < 90.0:
            payee.risk_level = "HIGH"
        else:
            payee.risk_level = "CRITICAL"

        payee.last_evaluated_at = datetime.now(timezone.utc)
        self.payee_repo.update(payee)

        # Record Risk Event
        risk_event = RiskEvent(
            entity_type="PAYEE",
            entity_id=payee.payee_vpa,
            event_type="REPORT_FILED",
            old_risk=old_risk,
            new_risk=payee.risk_score,
            reason=f"Fraud report filed under category: {req.category}"
        )
        self.payee_repo.add_risk_event(risk_event)

        # Audit log
        self.audit_repo.log(
            action=AuditAction.REPORT_SUBMITTED.value,
            user_id=reporter_user_id,
            entity_type="REPORT",
            entity_id=report.id,
            details={"payee_vpa": req.payee_vpa, "category": req.category, "new_risk": payee.risk_score},
            ip_address=ip_address
        )

        self.db.commit()
        return report

    def record_successful_transaction(self, payee_vpa: str):
        payee = self.payee_repo.get_or_create(payee_vpa)
        old_risk = payee.risk_score
        
        payee.total_transactions += 1
        payee.successful_transactions += 1
        
        # Gradual risk decay for successful behavior
        decay_amount = 2.0 if payee.risk_score > 30.0 else 0.5
        payee.risk_score = max(5.0, payee.risk_score - decay_amount)
        payee.reputation_score = min(100.0, 100.0 - payee.risk_score)
        
        if payee.risk_score < 40.0:
            payee.risk_level = "LOW"
        elif payee.risk_score < 70.0:
            payee.risk_level = "MEDIUM"
        else:
            payee.risk_level = "HIGH"

        payee.last_evaluated_at = datetime.now(timezone.utc)
        self.payee_repo.update(payee)

        if abs(old_risk - payee.risk_score) > 0.1:
            risk_event = RiskEvent(
                entity_type="PAYEE",
                entity_id=payee.payee_vpa,
                event_type="REPUTATION_UPDATE",
                old_risk=old_risk,
                new_risk=payee.risk_score,
                reason="Reputation improved following successful payment"
            )
            self.payee_repo.add_risk_event(risk_event)

        self.db.commit()

    def list_reports(self, skip: int = 0, limit: int = 50) -> List[FraudReport]:
        return self.report_repo.get_all(skip=skip, limit=limit)
