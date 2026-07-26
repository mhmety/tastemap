
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    restaurant_id: uuid.UUID
    user_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewResponse(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
