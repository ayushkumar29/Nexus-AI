"""Service handling user registration, authentication, and user queries."""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest

logger = logging.getLogger("nexus_ai.auth")


class AuthService:
    """Service layer encapsulating user and authentication business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        stmt = select(User).where(User.email == email.lower().strip())
        return self.db.scalars(stmt).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by primary key."""
        stmt = select(User).where(User.id == user_id)
        return self.db.scalars(stmt).first()

    def register_user(self, payload: UserRegisterRequest) -> User:
        """Register a new user with Argon2 hashed password."""
        normalized_email = payload.email.lower().strip()

        # Check for existing user with same email
        existing_user = self.get_by_email(normalized_email)
        if existing_user:
            raise AppException(
                message="A user with this email address already exists.",
                status_code=409,
            )

        # Hash password securely
        hashed_pw = hash_password(payload.password)

        new_user = User(
            full_name=payload.full_name.strip(),
            email=normalized_email,
            hashed_password=hashed_pw,
            is_active=True,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        logger.info(f"Registered new user id={new_user.id} email={new_user.email}")
        return new_user

    def authenticate_user(self, payload: UserLoginRequest) -> TokenResponse:
        """Authenticate user credentials and return signed JWT."""
        normalized_email = payload.email.lower().strip()
        user = self.get_by_email(normalized_email)

        if not user or not verify_password(payload.password, user.hashed_password):
            # Constant-time-like or safe generic failure message
            raise AppException(
                message="Invalid email or password.",
                status_code=401,
            )

        if not user.is_active:
            raise AppException(
                message="User account is inactive.",
                status_code=403,
            )

        token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email},
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
