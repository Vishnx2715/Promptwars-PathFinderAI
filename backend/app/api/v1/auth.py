from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    user, token = await AuthService.register(db, data)
    AuthService.set_auth_cookie(response, token)
    return TokenResponse(
        message="Registration successful",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    user, token = await AuthService.login(db, data)
    AuthService.set_auth_cookie(response, token)
    return TokenResponse(
        message="Login successful",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout(response: Response):
    AuthService.clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
