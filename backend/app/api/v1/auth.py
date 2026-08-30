from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_client_ip
from backend.app.schemas.auth import LoginRequest, RegisterRequest, Token
from backend.app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    auth_service = AuthService(db)
    return auth_service.register(req, ip_address=ip)


@router.post("/login", response_model=Token)
def login(
    req: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    auth_service = AuthService(db)
    return auth_service.login(req, ip_address=ip)
