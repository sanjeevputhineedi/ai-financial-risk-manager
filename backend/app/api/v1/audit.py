from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_admin
from backend.app.models.user import User
from backend.app.schemas.audit import AuditLogRead
from backend.app.services.audit_service import AuditService

router = APIRouter()


@router.get("", response_model=List[AuditLogRead])
def list_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    audit_service = AuditService(db)
    return audit_service.get_logs(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        skip=skip,
        limit=limit
    )
