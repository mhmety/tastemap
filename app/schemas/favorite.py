
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FavoriteCreate(BaseModel):
    restaurant_id: uuid.UUID = Field(
        description="Identifier of the restaurant to add to favorites.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "restaurant_id": "4b4733c3-1136-4105-a957-dd4ed1cab0e2",
            }
        }
    )


class FavoriteResponse(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier of the favorite entry.")
    user_id: uuid.UUID = Field(description="Identifier of the user who owns the favorite entry.")
    restaurant_id: uuid.UUID = Field(description="Identifier of the favorited restaurant.")
    created_at: datetime = Field(description="Timestamp when the favorite entry was created.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "9c3a2222-aaaa-4f52-bbbb-1234567890ab",
                "user_id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
                "restaurant_id": "4b4733c3-1136-4105-a957-dd4ed1cab0e2",
                "created_at": "2026-07-27T10:00:00Z",
            }
        },
    )
