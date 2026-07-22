
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

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

