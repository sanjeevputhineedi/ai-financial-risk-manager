from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_current_active_admin, get_client_ip
from backend.app.models.user import User
from backend.app.schemas.fund_manager import HeldPaymentRead, ReleaseRefundRequest
from backend.app.services.fund_manager_service import FundManagerService
from backend.app.services.cooling_service import DynamicCoolingService

router = APIRouter()


@router.get("", response_model=List[HeldPaymentRead])
def list_held_payments(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    fm_service = FundManagerService(db)
    return fm_service.list_held_payments(skip=skip, limit=limit)


@router.get("/{id}", response_model=HeldPaymentRead)
def get_held_payment(
    id: str,
    db: Session = Depends(get_db)
):
    fm_service = FundManagerService(db)
    return fm_service.get_held_payment(id)


@router.post("/{id}/release", response_model=HeldPaymentRead)
def release_held_payment(
    id: str,
    req: ReleaseRefundRequest,
    request: Request,
    admin_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    fm_service = FundManagerService(db)
    return fm_service.release_funds(
        held_id=id,
        reason=req.reason,
        admin_user_id=admin_user.id,
        ip_address=ip
    )


@router.post("/{id}/refund", response_model=HeldPaymentRead)
def refund_held_payment(
    id: str,
    req: ReleaseRefundRequest,
    request: Request,
    admin_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    fm_service = FundManagerService(db)
    return fm_service.refund_funds(
        held_id=id,
        reason=req.reason,
        admin_user_id=admin_user.id,
        ip_address=ip
    )


@router.post("/reevaluate", response_model=List[Dict[str, Any]])
def reevaluate_held_payments(
    db: Session = Depends(get_db)
):
    """
    Checkpoint M8: Dynamic Cooling Period re-evaluation.
    Re-scans all active held transactions and resolves funds if risk changed.
    """
    cooling_service = DynamicCoolingService(db)
    return cooling_service.reevaluate_held_transactions()
