
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, create_refresh_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Unique email address
    - **password**: Password (8-128 characters)
    """
    # Check if username already exists
    username_exists = db.execute(
        select(User).where(User.username == user.username)
    ).scalar_one_or_none()
    
    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    normalized_email = user.email.lower()
    # Check if email already exists
    email_exists = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()
    
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password and create user
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


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK,)
def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access and refresh tokens.
    
    - **email**: User email address
    - **password**: User password
    """
    # Normalize email to lowercase
    normalized_email = user_login.email.lower()
    
    # Find user by email
    user = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

