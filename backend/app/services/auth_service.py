import uuid
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.core.errors import AuthenticationError, AppException
from backend.app.models.user import User
from backend.app.models.account import Account
from backend.app.models.audit_log import AuditAction
from backend.app.repositories.user_repo import UserRepository
from backend.app.repositories.account_repo import AccountRepository
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.schemas.auth import LoginRequest, RegisterRequest, Token


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.account_repo = AccountRepository(db)
        self.audit_repo = AuditRepository(db)

    def register(self, req: RegisterRequest, ip_address: Optional[str] = None) -> Token:
        if self.user_repo.get_by_email(req.email):
            raise AppException("Email is already registered", status_code=400, error_code="EMAIL_EXISTS")
        
        if self.user_repo.get_by_username(req.username):
            raise AppException("Username is already taken", status_code=400, error_code="USERNAME_EXISTS")

        hashed_pwd = get_password_hash(req.password)
        user = User(
            email=req.email,
            username=req.username,
            full_name=req.full_name,
            hashed_password=hashed_pwd,
            role="USER"
        )
        self.db.add(user)
        self.db.flush()

        # Create simulated UPI account
        upi_id = req.upi_id or f"{req.username}@upi"
        account_number = f"SIMU_ACC_{uuid.uuid4().hex[:8].upper()}"
        account = Account(
            user_id=user.id,
            upi_id=upi_id,
            account_number=account_number,
            balance=req.initial_balance,
            currency="INR"
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(user)

        self.audit_repo.log(
            action="USER_REGISTERED",
            user_id=user.id,
            entity_type="USER",
            entity_id=user.id,
            details={"email": user.email, "username": user.username, "initial_balance": req.initial_balance},
            ip_address=ip_address
        )

        token = create_access_token(user.id)
        return Token(
            access_token=token,
            expires_in=60 * 24 * 60,
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role
        )

    def login(self, req: LoginRequest, ip_address: Optional[str] = None) -> Token:
        user = self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        self.audit_repo.log(
            action=AuditAction.LOGIN.value,
            user_id=user.id,
            entity_type="USER",
            entity_id=user.id,
            details={"email": user.email},
            ip_address=ip_address
        )

        token = create_access_token(user.id)
        return Token(
            access_token=token,
            expires_in=60 * 24 * 60,
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role
        )
