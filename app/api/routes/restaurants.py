
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.schemas.restaurant import (
    RestaurantDetailResponse,
    RestaurantResponse,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=List[RestaurantResponse])
def list_restaurants(
    city: Annotated[Optional[str], Query(description="Filter by city")] = None,
    district: Annotated[Optional[str], Query(description="Filter by district")] = None,
    category: Annotated[Optional[str], Query(description="Filter by menu item category")] = None,
    db: Session = Depends(get_db),
):
    """
    List restaurants with optional filters.

    - **city**: Filter restaurants located in the given city.
    - **district**: Filter restaurants located in the given district.
    - **category**: Filter restaurants that have at least one menu item in this category.
    """
    query = select(Restaurant)

    if city is not None:
        query = query.where(Restaurant.city == city)

    if district is not None:
        query = query.where(Restaurant.district == district)

    if category is not None:
        query = query.join(Restaurant.menu_items).where(MenuItem.category == category)
        query = query.distinct()

    result = db.execute(query)
    restaurants = result.scalars().all()
    return list(restaurants)


@router.get("/{restaurant_id}", response_model=RestaurantDetailResponse)
def get_restaurant_detail(
    restaurant_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a restaurant.

    - **restaurant_id**: UUID of the restaurant to retrieve.

    Includes:
    - Basic restaurant information
    - Full menu items list
    - All reviews with ratings and comments
    - Dynamically computed average_rating and review_count
    """
    query = (
        select(Restaurant)
        .options(
            selectinload(Restaurant.menu_items),
            selectinload(Restaurant.reviews),
        )
        .where(Restaurant.id == restaurant_id)
    )

    result = db.execute(query)
    restaurant = result.scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    reviews = restaurant.reviews
    review_count = len(reviews)
    if review_count > 0:
        average_rating = round(sum(r.rating for r in reviews) / review_count, 2)
    else:
        average_rating = None

    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "city": restaurant.city,
        "district": restaurant.district,
        "latitude": restaurant.latitude,
        "longitude": restaurant.longitude,
        "website": restaurant.website,
        "phone": restaurant.phone,
        "description": restaurant.description,
        "created_at": restaurant.created_at,
        "updated_at": restaurant.updated_at,
        "average_rating": average_rating,
        "review_count": review_count,
        "menu_items": list(restaurant.menu_items),
        "reviews": list(reviews),
    }
