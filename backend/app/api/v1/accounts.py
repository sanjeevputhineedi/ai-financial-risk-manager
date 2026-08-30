from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.account import AccountRead, RecipientRead, RecipientCreate
from backend.app.services.account_service import AccountService

router = APIRouter()
recipients_router = APIRouter()


@router.get("/me", response_model=AccountRead)
def get_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account_service = AccountService(db)
    return account_service.get_account_by_user(current_user.id)


@recipients_router.get("", response_model=List[RecipientRead])
def get_my_recipients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account_service = AccountService(db)
    return account_service.get_recipients(current_user.id)


@recipients_router.post("", response_model=RecipientRead, status_code=status.HTTP_201_CREATED)
def add_recipient(
    req: RecipientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account_service = AccountService(db)
    return account_service.add_recipient(current_user.id, req)
