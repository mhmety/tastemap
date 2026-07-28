
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Unique username for the new account.",
    )
    email: EmailStr = Field(
        description="Email address used for authentication and account communication.",
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plain-text password that will be hashed before storage.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "mehmetyildiz",
                "email": "mehmet@example.com",
                "password": "StrongPass123!",
            }
        }
    )


class UserLogin(BaseModel):
    email: EmailStr = Field(
        description="Registered email address used to sign in.",
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plain-text password for the account.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "mehmet@example.com",
                "password": "StrongPass123!",
            }
        }
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(
        description="Registered email address used to sign in.",
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plain-text password for the account.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "mehmet@example.com",
                "password": "StrongPass123!",
            }
        }
    )


class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Authenticated user identifier extracted from the JWT subject claim.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
            }
        }
    )


class Token(BaseModel):
    access_token: str = Field(
        description="JWT access token used for authenticated API requests.",
    )
    token_type: str = Field(
        default="bearer",
        description="Authentication scheme type for the returned token.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example",
                "token_type": "bearer",
            }
        }
    )


class UserResponse(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier of the user account.")
    username: str = Field(description="Unique username of the account.")
    email: EmailStr = Field(description="Email address associated with the account.")
    is_active: bool = Field(description="Whether the user account is currently active.")
    is_admin: bool = Field(description="Whether the user has administrator privileges.")
    created_at: datetime = Field(description="Timestamp when the user account was created.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
                "username": "mehmetyildiz",
                "email": "mehmet@example.com",
                "is_active": True,
                "is_admin": False,
                "created_at": "2026-07-27T10:00:00Z",
            }
        },
    )


class TokenResponse(BaseModel):
    access_token: str = Field(
        description="JWT access token used in the Authorization header.",
    )
    refresh_token: str = Field(
        description="JWT refresh token that can be used for future token renewal flows.",
    )
    token_type: str = Field(
        default="bearer",
        description="Authentication scheme type for the returned tokens.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
                "token_type": "bearer",
            }
        }
    )
