from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.models.user import User
from backend.app.schemas.report import FraudReportCreate, FraudReportRead
from backend.app.services.reputation_service import ReputationService

router = APIRouter()


@router.post("", response_model=FraudReportRead, status_code=status.HTTP_201_CREATED)
def submit_fraud_report(
    req: FraudReportCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    rep_service = ReputationService(db)
    return rep_service.create_fraud_report(current_user.id, req, ip_address=ip)


@router.get("", response_model=List[FraudReportRead])
def list_fraud_reports(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    rep_service = ReputationService(db)
    return rep_service.list_reports(skip=skip, limit=limit)
