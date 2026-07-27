
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=1000)


class RestaurantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    district: Optional[str] = Field(default=None, min_length=1, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=1000)


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
    average_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RestaurantListResponse(BaseModel):
    items: List[RestaurantResponse]
    total: int
    limit: int
    offset: int


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
