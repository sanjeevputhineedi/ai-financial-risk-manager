from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog
from backend.app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        # Sanitize details to never include password or tokens
        clean_details = {}
        if details:
            for k, v in details.items():
                if any(secret_term in k.lower() for secret_term in ["password", "token", "secret", "authorization"]):
                    clean_details[k] = "[REDACTED]"
                else:
                    clean_details[k] = v

        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            details=clean_details,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(audit_entry)
        self.db.commit()
        self.db.refresh(audit_entry)
        return audit_entry

    def get_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        query = self.db.query(AuditLog)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
