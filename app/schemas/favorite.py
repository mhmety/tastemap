
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FavoriteCreate(BaseModel):
    restaurant_id: uuid.UUID


class FavoriteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    restaurant_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
