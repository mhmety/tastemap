
import uuid
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import CurrentAdmin
from app.db.session import get_db
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantDetailResponse,
    RestaurantListResponse,
    RestaurantResponse,
    RestaurantUpdate,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


def _build_average_rating_subquery():
    return (
        select(
            Review.restaurant_id.label("restaurant_id"),
            func.avg(Review.rating).label("average_rating"),
        )
        .group_by(Review.restaurant_id)
        .subquery()
    )


def _apply_restaurant_list_filters(
    query,
    average_rating_subquery,
    search: Optional[str],
    city: Optional[str],
    district: Optional[str],
    category: Optional[str],
    minimum_rating: Optional[float],
):
    search_term = search.strip() if search else None
    if search_term:
        pattern = f"%{search_term}%"
        query = query.where(
            or_(
                Restaurant.name.ilike(pattern),
                Restaurant.description.ilike(pattern),
                # Use relationship filters so matching menu items do not duplicate restaurants.
                Restaurant.menu_items.any(MenuItem.name.ilike(pattern)),
            )
        )

    if city is not None:
        query = query.where(Restaurant.city == city)

    if district is not None:
        query = query.where(Restaurant.district == district)

    if category is not None:
        query = query.where(Restaurant.menu_items.any(MenuItem.category == category))

    if minimum_rating is not None:
        query = query.where(
            average_rating_subquery.c.average_rating >= minimum_rating
        )

    return query


def _apply_restaurant_list_sorting(query, average_rating_subquery, sort: str):
    if sort == "name":
        return query.order_by(Restaurant.name.asc(), Restaurant.created_at.desc())

    if sort == "rating":
        return query.order_by(
            average_rating_subquery.c.average_rating.desc().nullslast(),
            Restaurant.created_at.desc(),
        )

    return query.order_by(Restaurant.created_at.desc())


def _serialize_restaurant_list_item(
    restaurant: Restaurant,
    average_rating: Optional[float],
) -> RestaurantResponse:
    return RestaurantResponse.model_validate(
        {
            "id": restaurant.id,
            "name": restaurant.name,
            "city": restaurant.city,
            "district": restaurant.district,
            "latitude": restaurant.latitude,
            "longitude": restaurant.longitude,
            "website": restaurant.website,
            "phone": restaurant.phone,
            "description": restaurant.description,
            "average_rating": average_rating,
            "created_at": restaurant.created_at,
            "updated_at": restaurant.updated_at,
        }
    )


@router.get("", response_model=RestaurantListResponse)
def list_restaurants(
    search: Annotated[
        Optional[str],
        Query(description="Search by restaurant name, description, or menu item name"),
    ] = None,
    city: Annotated[Optional[str], Query(description="Filter by city")] = None,
    district: Annotated[Optional[str], Query(description="Filter by district")] = None,
    category: Annotated[Optional[str], Query(description="Filter by menu item category")] = None,
    minimum_rating: Annotated[
        Optional[float],
        Query(ge=1, le=5, description="Filter by minimum average review rating"),
    ] = None,
    sort: Annotated[
        Literal["name", "rating", "created_at"],
        Query(description="Sort field"),
    ] = "created_at",
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of restaurants to return"),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of restaurants to skip"),
    ] = 0,
    db: Session = Depends(get_db),
):
    """
    List restaurants with optional search, filters, sorting, and pagination
    (public endpoint).

    - **search**: Case-insensitive search on restaurant name, description, and menu item name.
    - **city**: Filter restaurants located in the given city.
    - **district**: Filter restaurants located in the given district.
    - **category**: Filter restaurants that have at least one menu item in this category.
    - **minimum_rating**: Filter restaurants whose average review rating is at least this value.
    - **sort**: Sort by `name`, `rating`, or `created_at`.
    - **limit / offset**: Pagination controls.
    """
    average_rating_subquery = _build_average_rating_subquery()
    average_rating_column = average_rating_subquery.c.average_rating.label("average_rating")
    restaurant_query = (
        select(Restaurant, average_rating_column)
        .outerjoin(
            average_rating_subquery,
            average_rating_subquery.c.restaurant_id == Restaurant.id,
        )
    )

    restaurant_query = _apply_restaurant_list_filters(
        restaurant_query,
        average_rating_subquery,
        search,
        city,
        district,
        category,
        minimum_rating,
    )
    restaurant_query = _apply_restaurant_list_sorting(
        restaurant_query,
        average_rating_subquery,
        sort,
    )

    total_query = select(func.count()).select_from(
        restaurant_query.order_by(None).subquery()
    )
    total = db.execute(total_query).scalar_one()

    restaurant_query = restaurant_query.limit(limit).offset(offset)

    result = db.execute(restaurant_query)
    rows = result.all()

    items = [
        _serialize_restaurant_list_item(restaurant, average_rating)
        for restaurant, average_rating in rows
    ]

    return RestaurantListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{restaurant_id}", response_model=RestaurantDetailResponse)
def get_restaurant_detail(
    restaurant_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a restaurant (public endpoint).

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


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    data: RestaurantCreate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """
    Create a new restaurant (admin only).

    Requires admin privileges. Unauthenticated requests return 401;
    non-admin authenticated requests return 403.

    - **name**: Restaurant name (required, 1-255 characters)
    - **city**: City where the restaurant is located (required, 1-100 characters)
    - **district**: District where the restaurant is located (required, 1-100 characters)
    - **latitude / longitude**: Optional geographic coordinates
    - **website / phone / description**: Optional contact and information fields
    """
    restaurant = Restaurant(
        name=data.name,
        city=data.city,
        district=data.district,
        latitude=data.latitude,
        longitude=data.longitude,
        website=data.website,
        phone=data.phone,
        description=data.description,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: uuid.UUID,
    data: RestaurantUpdate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """
    Update an existing restaurant (admin only).

    Only fields provided in the request body will be updated.
    All other fields remain unchanged.

    - **restaurant_id**: UUID of the restaurant to update
    """
    query = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = db.execute(query)
    restaurant = result.scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)

    return restaurant


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(
    restaurant_id: uuid.UUID,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """
    Delete a restaurant (admin only).

    All associated menu items, reviews, and favorites are automatically
    removed through cascade delete configuration.

    - **restaurant_id**: UUID of the restaurant to delete
    """
    query = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = db.execute(query)
    restaurant = result.scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    db.delete(restaurant)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
