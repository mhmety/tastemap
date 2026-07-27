
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Burger House",
                "city": "Ankara",
                "district": "Cankaya",
                "latitude": 39.9334,
                "longitude": 32.8597,
                "website": "https://burgerhouse.com",
                "phone": "+90 312 123 45 67",
                "description": "Casual burger restaurant with signature house sauces.",
            }
        }
    )


class RestaurantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    district: Optional[str] = Field(default=None, min_length=1, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=1000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone": "+90 312 987 65 43",
                "description": "Updated description for the restaurant profile.",
            }
        }
    )


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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "4b4733c3-1136-4105-a957-dd4ed1cab0e2",
                "name": "Burger House",
                "city": "Ankara",
                "district": "Cankaya",
                "latitude": 39.9334,
                "longitude": 32.8597,
                "website": "https://burgerhouse.com",
                "phone": "+90 312 123 45 67",
                "description": "Casual burger restaurant with signature house sauces.",
                "average_rating": 4.6,
                "created_at": "2026-07-27T10:00:00Z",
                "updated_at": "2026-07-27T10:00:00Z",
            }
        },
    )


class RestaurantListResponse(BaseModel):
    items: List[RestaurantResponse]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "4b4733c3-1136-4105-a957-dd4ed1cab0e2",
                        "name": "Burger House",
                        "city": "Ankara",
                        "district": "Cankaya",
                        "latitude": 39.9334,
                        "longitude": 32.8597,
                        "website": "https://burgerhouse.com",
                        "phone": "+90 312 123 45 67",
                        "description": "Casual burger restaurant with signature house sauces.",
                        "average_rating": 4.6,
                        "created_at": "2026-07-27T10:00:00Z",
                        "updated_at": "2026-07-27T10:00:00Z",
                    }
                ],
                "total": 124,
                "limit": 20,
                "offset": 40,
            }
        }
    )


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
