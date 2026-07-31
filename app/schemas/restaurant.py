
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RestaurantCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Display name of the restaurant.",
    )
    city: str = Field(
        min_length=1,
        max_length=100,
        description="City where the restaurant is located.",
    )
    district: str = Field(
        min_length=1,
        max_length=100,
        description="District or neighborhood where the restaurant is located.",
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Optional latitude coordinate of the restaurant location.",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Optional longitude coordinate of the restaurant location.",
    )
    website: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional public website URL for the restaurant.",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional public phone number for the restaurant.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional marketing description or summary of the restaurant.",
    )

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
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated display name of the restaurant.",
    )
    city: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated city for the restaurant.",
    )
    district: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated district or neighborhood for the restaurant.",
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Updated latitude coordinate of the restaurant location.",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Updated longitude coordinate of the restaurant location.",
    )
    website: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Updated public website URL for the restaurant.",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Updated public phone number for the restaurant.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Updated restaurant description.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone": "+90 312 987 65 43",
                "description": "Updated description for the restaurant profile.",
            }
        }
    )


class RestaurantResponse(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier of the restaurant.")
    name: str = Field(description="Display name of the restaurant.")
    city: str = Field(description="City where the restaurant is located.")
    district: str = Field(description="District or neighborhood of the restaurant.")
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude coordinate of the restaurant, when available.",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude coordinate of the restaurant, when available.",
    )
    website: Optional[str] = Field(
        default=None,
        description="Public website URL of the restaurant, when available.",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Public phone number of the restaurant, when available.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Short description of the restaurant.",
    )
    rating: Optional[float] = Field(
        default=None,
        description="External rating imported from providers (e.g., Google), or null if missing.",
    )
    review_count: Optional[int] = Field(
        default=None,
        description="External review count imported from providers, or null if missing.",
    )
    category: Optional[str] = Field(
        default=None,
        description="External category/type label for the restaurant, when available.",
    )
    google_place_id: Optional[str] = Field(
        default=None,
        description="Google Place ID (or equivalent provider identifier), when available.",
    )
    thumbnail: Optional[str] = Field(
        default=None,
        description="Thumbnail image URL for the restaurant, when available.",
    )
    opening_hours: Optional[str] = Field(
        default=None,
        description="Opening hours information as provided by the source, when available.",
    )
    average_rating: Optional[float] = Field(
        default=None,
        description="Average rating calculated from reviews, or null if unrated.",
    )
    created_at: datetime = Field(description="Timestamp when the restaurant was created.")
    updated_at: datetime = Field(description="Timestamp when the restaurant was last updated.")

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
    items: List[RestaurantResponse] = Field(
        description="Paginated restaurant records for the current query.",
    )
    total: int = Field(description="Total number of matching restaurants before pagination.")
    limit: int = Field(description="Maximum number of restaurants returned in this page.")
    offset: int = Field(description="Number of matching restaurants skipped before this page.")

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
    id: uuid.UUID = Field(description="Unique identifier of the menu item.")
    name: str = Field(description="Display name of the menu item.")
    price: float = Field(description="Current price of the menu item.")
    category: str = Field(description="Category assigned to the menu item.")
    description: Optional[str] = Field(
        default=None,
        description="Optional description of the menu item.",
    )
    created_at: datetime = Field(description="Timestamp when the menu item was created.")
    updated_at: datetime = Field(description="Timestamp when the menu item was last updated.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": "Pepperoni Pizza",
                "price": 19.99,
                "category": "Pizza",
                "description": "Stone-baked pizza with pepperoni and mozzarella.",
                "created_at": "2026-07-27T10:00:00Z",
                "updated_at": "2026-07-27T10:00:00Z",
            }
        },
    )


class ReviewResponse(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier of the review.")
    user_id: uuid.UUID = Field(description="Identifier of the user who wrote the review.")
    rating: int = Field(description="Rating value from 1 to 5.")
    comment: Optional[str] = Field(
        default=None,
        description="Optional written comment for the review.",
    )
    created_at: datetime = Field(description="Timestamp when the review was created.")
    updated_at: datetime = Field(description="Timestamp when the review was last updated.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "33333333-3333-3333-3333-333333333333",
                "user_id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
                "rating": 5,
                "comment": "Excellent burgers and quick service.",
                "created_at": "2026-07-27T10:00:00Z",
                "updated_at": "2026-07-27T10:00:00Z",
            }
        },
    )


class RestaurantDetailResponse(BaseModel):
    id: uuid.UUID = Field(description="Unique identifier of the restaurant.")
    name: str = Field(description="Display name of the restaurant.")
    city: str = Field(description="City where the restaurant is located.")
    district: str = Field(description="District or neighborhood of the restaurant.")
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude coordinate of the restaurant, when available.",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude coordinate of the restaurant, when available.",
    )
    website: Optional[str] = Field(
        default=None,
        description="Public website URL of the restaurant, when available.",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Public phone number of the restaurant, when available.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Short description of the restaurant.",
    )
    rating: Optional[float] = Field(
        default=None,
        description="External rating imported from providers (e.g., Google), or null if missing.",
    )
    category: Optional[str] = Field(
        default=None,
        description="External category/type label for the restaurant, when available.",
    )
    google_place_id: Optional[str] = Field(
        default=None,
        description="Google Place ID (or equivalent provider identifier), when available.",
    )
    thumbnail: Optional[str] = Field(
        default=None,
        description="Thumbnail image URL for the restaurant, when available.",
    )
    opening_hours: Optional[str] = Field(
        default=None,
        description="Opening hours information as provided by the source, when available.",
    )
    created_at: datetime = Field(description="Timestamp when the restaurant was created.")
    updated_at: datetime = Field(description="Timestamp when the restaurant was last updated.")
    average_rating: Optional[float] = Field(
        default=None,
        description="Average rating calculated from all reviews, or null if unrated.",
    )
    review_count: int = Field(
        description="Total number of reviews (external provider count if available; otherwise TasteMap review count)."
    )
    menu_items: List[MenuItemResponse] = Field(
        description="Menu items currently associated with the restaurant.",
    )
    reviews: List[ReviewResponse] = Field(
        description="Published reviews currently associated with the restaurant.",
    )

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
                "created_at": "2026-07-27T10:00:00Z",
                "updated_at": "2026-07-27T10:00:00Z",
                "average_rating": 4.6,
                "review_count": 18,
                "menu_items": [
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "name": "Pepperoni Pizza",
                        "price": 19.99,
                        "category": "Pizza",
                        "description": "Stone-baked pizza with pepperoni and mozzarella.",
                        "created_at": "2026-07-27T10:00:00Z",
                        "updated_at": "2026-07-27T10:00:00Z",
                    }
                ],
                "reviews": [
                    {
                        "id": "33333333-3333-3333-3333-333333333333",
                        "user_id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
                        "rating": 5,
                        "comment": "Excellent burgers and quick service.",
                        "created_at": "2026-07-27T10:00:00Z",
                        "updated_at": "2026-07-27T10:00:00Z",
                    }
                ],
            }
        },
    )
