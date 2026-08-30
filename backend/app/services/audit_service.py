from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog
from backend.app.repositories.audit_repo import AuditRepository


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_repo = AuditRepository(db)

    def get_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        return self.audit_repo.get_logs(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            skip=skip,
            limit=limit
        )
