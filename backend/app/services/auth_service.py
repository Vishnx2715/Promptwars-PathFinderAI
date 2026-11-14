from datetime import timedelta
from fastapi import HTTPException, status, Response
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.profile import StudentProfile
from app.schemas.auth import UserRegister, UserLogin


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, data: UserRegister) -> tuple[User, str]:
        # Check if email or username exists
        res = await db.execute(
            select(User).where(or_(User.email == data.email.lower(), User.username == data.username))
        )
        existing = res.scalar_one_or_none()
        if existing:
            if existing.email == data.email.lower():
                raise HTTPException(status_code=400, detail="Email is already registered")
            else:
                raise HTTPException(status_code=400, detail="Username is already taken")

        hashed_pw = get_password_hash(data.password)
        new_user = User(
            email=data.email.lower(),
            username=data.username,
            hashed_password=hashed_pw,
            role="student",
            is_active=True
        )
        db.add(new_user)
        await db.flush()

        # Create linked StudentProfile
        profile = StudentProfile(
            user_id=new_user.id,
            full_name=data.username,
            weekly_study_hours=8,
            projects=[],
            certifications=[]
        )
        db.add(profile)
        await db.commit()
        await db.refresh(new_user)

        token = create_access_token(subject=str(new_user.id))
        return new_user, token

    @staticmethod
    async def login(db: AsyncSession, data: UserLogin) -> tuple[User, str]:
        identifier = data.username_or_email.strip().lower()
        res = await db.execute(
            select(User).where(
                or_(User.email == identifier, User.username == data.username_or_email.strip())
            )
        )
        user = res.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            # Generic authentication error for security
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive."
            )

        token = create_access_token(subject=str(user.id))
        return user, token

    @staticmethod
    def set_auth_cookie(response: Response, token: str) -> None:
        max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=settings.SECURE_COOKIE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=max_age,
            path="/"
        )

    @staticmethod
    def clear_auth_cookie(response: Response) -> None:
        response.delete_cookie(
            key="access_token",
            path="/"
        )
