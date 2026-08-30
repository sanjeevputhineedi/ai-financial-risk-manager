from fastapi import APIRouter, Depends
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.user import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
