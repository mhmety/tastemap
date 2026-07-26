
import uuid
from datetime import datetime
from typing import List, Optional

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


class MenuItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    price: float
    category: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RestaurantDetailResponse(BaseModel):
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
    average_rating: Optional[float] = None
    review_count: int
    menu_items: List[MenuItemResponse]
    reviews: List[ReviewResponse]

    model_config = ConfigDict(from_attributes=True)
