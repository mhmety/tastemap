
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RestaurantResponse(BaseModel):
    id: uuid.UUID
    name: str
    city: str
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
