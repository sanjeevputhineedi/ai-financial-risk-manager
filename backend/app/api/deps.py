from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.core.errors import AuthenticationError, PermissionDeniedError
from backend.app.models.user import User
from backend.app.repositories.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    if not token:
        raise AuthenticationError("Not authenticated. Bearer token required.")
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise AuthenticationError("Could not validate credentials or token expired")
    
    user_id = payload["sub"]
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)
    if not user:
        raise AuthenticationError("User associated with token not found")
    
    if not user.is_active:
        raise AuthenticationError("User is inactive")
    
    return user


def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role not in ["ADMIN", "RESEARCHER"]:
        raise PermissionDeniedError("Admin privileges required for this operation")
    return current_user


def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
