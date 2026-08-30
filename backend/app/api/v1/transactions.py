from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.models.user import User
from backend.app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionConfirmRequest,
    TransactionCancelRequest
)
from backend.app.services.transaction_service import TransactionService

router = APIRouter()


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    req: TransactionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    tx_service = TransactionService(db)
    return tx_service.create_transaction(current_user.id, req, ip_address=ip)


@router.get("", response_model=List[TransactionRead])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx_service = TransactionService(db)
    return tx_service.list_transactions_for_user(current_user.id)


@router.get("/{id}", response_model=TransactionRead)
def get_transaction(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx_service = TransactionService(db)
    return tx_service.get_transaction_by_id(id)


@router.post("/{id}/confirm", response_model=TransactionRead)
def confirm_transaction(
    id: str,
    req: TransactionConfirmRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    tx_service = TransactionService(db)
    return tx_service.confirm_transaction(id, current_user.id, req, ip_address=ip)


@router.post("/{id}/cancel", response_model=TransactionRead)
def cancel_transaction(
    id: str,
    req: TransactionCancelRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    tx_service = TransactionService(db)
    return tx_service.cancel_transaction(id, current_user.id, req.reason, ip_address=ip)
