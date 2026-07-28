
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, create_refresh_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    description="Create a new user account with a unique username and email address.",
    response_description="The newly created user account.",
    responses={
        201: {
            "description": "User account created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
                        "username": "mehmetyildiz",
                        "email": "mehmet@example.com",
                        "is_active": True,
                        "is_admin": False,
                        "created_at": "2026-07-27T10:00:00Z",
                    }
                }
            },
        },
        409: {
            "description": "Username or email is already registered.",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            },
        },
        422: {"description": "Validation error in the submitted payload."},
    },
)
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    """
    Register a new user account.

    - **username**: Unique username (3-50 characters)
    - **email**: Unique email address
    - **password**: Password (8-128 characters)
    """
    username_exists = db.execute(
        select(User).where(User.username == user.username)
    ).scalar_one_or_none()

    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )

    normalized_email = user.email.lower()
    email_exists = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()

    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    hashed_pwd = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=normalized_email,
        hashed_password=hashed_pwd
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in a user",
    description=(
        "Authenticate a user using the OAuth2 password flow and return JWT access and refresh tokens."
    ),
    response_description="JWT access and refresh tokens.",
    responses={
        200: {
            "description": "Login successful.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials or inactive user account.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password"}
                }
            },
        },
        422: {"description": "Validation error in submitted form data."},
    },
)
def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    OAuth2 compatible token login.

    Accepts form-encoded username (treated as email) and password, then returns
    a JWT access token and refresh token. Works with the Swagger UI "Authorize"
    button out of the box.

    - **username**: User email address (lowercased before lookup)
    - **password**: User password
    """
    normalized_email = form_data.username.lower()

    user = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )
