
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

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
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "mehmet@example.com",
                "password": "StrongPass123!",
            }
        }
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "mehmet@example.com",
                "password": "StrongPass123!",
            }
        }
    )


class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
            }
        }
    )


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example",
                "token_type": "bearer",
            }
        }
    )


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime

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
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
                "token_type": "bearer",
            }
        }
    )
