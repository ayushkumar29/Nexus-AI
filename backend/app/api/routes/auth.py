"""Authentication routes (registration, login, and current user profile)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(db)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Registers a new user with email, full name, and Argon2-hashed password.",
)
async def register(
    payload: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Register a new user."""
    user = auth_service.register_user(payload)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User",
    description="Authenticates credentials and returns a signed JWT access token.",
)
async def login(
    payload: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate and obtain JWT access token."""
    return auth_service.authenticate_user(payload)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve profile for currently authenticated user."""
    return UserResponse.model_validate(current_user)
