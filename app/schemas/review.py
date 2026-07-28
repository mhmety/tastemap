
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    restaurant_id: uuid.UUID = Field(
        description="Identifier of the restaurant being reviewed.",
    )
    rating: int = Field(
        ge=1,
        le=5,
        description="Numeric rating from 1 to 5.",
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional written review comment.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "restaurant_id": "4b4733c3-1136-4105-a957-dd4ed1cab0e2",
                "rating": 5,
                "comment": "Excellent burgers and quick service.",
            }
        }
    )


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Updated numeric rating from 1 to 5.",
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Updated written review comment.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 4,
                "comment": "Updated review after a second visit.",
            }
        }
    )


class ReviewResponse(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier of the review.")
    restaurant_id: uuid.UUID = Field(description="Identifier of the reviewed restaurant.")
    user_id: uuid.UUID = Field(description="Identifier of the user who created the review.")
    rating: int = Field(description="Numeric rating from 1 to 5.")
    comment: Optional[str] = Field(
        default=None,
        description="Optional written review comment.",
    )
    created_at: datetime = Field(description="Timestamp when the review was created.")
    updated_at: datetime = Field(description="Timestamp when the review was last updated.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "33333333-3333-3333-3333-333333333333",
                "restaurant_id": "4b4733c3-1136-4105-a957-dd4ed1cab0e2",
                "user_id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
                "rating": 5,
                "comment": "Excellent burgers and quick service.",
                "created_at": "2026-07-27T10:00:00Z",
                "updated_at": "2026-07-27T10:00:00Z",
            }
        },
    )
