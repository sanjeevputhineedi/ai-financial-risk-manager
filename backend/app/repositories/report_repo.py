from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.fraud_report import FraudReport
from backend.app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[FraudReport]):
    def __init__(self, db: Session):
        super().__init__(FraudReport, db)

    def get_by_payee_vpa(self, payee_vpa: str) -> List[FraudReport]:
        return self.db.query(FraudReport).filter(FraudReport.payee_vpa == payee_vpa).all()

    def get_by_reporter(self, user_id: str) -> List[FraudReport]:
        return self.db.query(FraudReport).filter(FraudReport.reporter_user_id == user_id).all()

    def count_reports_for_payee(self, payee_vpa: str) -> int:
        return self.db.query(FraudReport).filter(FraudReport.payee_vpa == payee_vpa).count()
