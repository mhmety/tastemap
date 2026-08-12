
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.selectable import Subquery

from app.api.deps import CurrentAdmin, CurrentUser
from app.db.session import get_db
from app.models.google_review import GoogleReview
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.review import RestaurantReviewCreate, ReviewResponse
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantDetailResponse,
    RestaurantListResponse,
    RestaurantResponse,
    RestaurantUpdate,
)
from app.services.google_reviews_sync import google_review_to_review_response_payload

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _build_review_stats_subquery() -> Subquery:
    google_stats = (
        select(
            GoogleReview.restaurant_id.label("restaurant_id"),
            func.sum(GoogleReview.rating).label("rating_sum"),
            func.count(GoogleReview.rating).label("rated_count"),
            func.count(GoogleReview.id).label("review_count"),
        )
        .group_by(GoogleReview.restaurant_id)
        .subquery()
    )
    user_stats = (
        select(
            Review.restaurant_id.label("restaurant_id"),
            func.sum(Review.rating).label("rating_sum"),
            func.count(Review.rating).label("rated_count"),
            func.count(Review.id).label("review_count"),
        )
        .group_by(Review.restaurant_id)
        .subquery()
    )

    joined = google_stats.join(
        user_stats,
        google_stats.c.restaurant_id == user_stats.c.restaurant_id,
        full=True,
    )

    restaurant_id = func.coalesce(
        google_stats.c.restaurant_id,
        user_stats.c.restaurant_id,
    ).label("restaurant_id")
    rating_sum = func.coalesce(google_stats.c.rating_sum, 0) + func.coalesce(
        user_stats.c.rating_sum, 0
    )
    rated_count = func.coalesce(google_stats.c.rated_count, 0) + func.coalesce(
        user_stats.c.rated_count, 0
    )
    review_count = func.coalesce(google_stats.c.review_count, 0) + func.coalesce(
        user_stats.c.review_count, 0
    )

    average_rating = (rating_sum / func.nullif(rated_count, 0)).label("average_rating")

    return (
        select(
            restaurant_id,
            average_rating,
            review_count.label("review_count"),
        )
        .select_from(joined)
        .subquery()
    )


def _apply_restaurant_list_filters(
    query: Any,
    review_stats_subquery: Subquery,
    search: Optional[str],
    city: Optional[str],
    district: Optional[str],
    category: Optional[str],
    minimum_rating: Optional[float],
) -> Any:
    search_term = search.strip() if search else None
    if search_term:
        pattern = f"%{search_term}%"
        query = query.where(
            or_(
                Restaurant.name.ilike(pattern),
                Restaurant.description.ilike(pattern),
                Restaurant.city.ilike(pattern),
                Restaurant.district.ilike(pattern),
                Restaurant.category.ilike(pattern),
                # Use relationship filters so matching menu items do not duplicate restaurants.
                Restaurant.menu_items.any(MenuItem.name.ilike(pattern)),
                # Search restaurants by foods mentioned inside review comments (no JOIN; avoids duplicates).
                Restaurant.reviews.any(Review.comment.ilike(pattern)),
                # Search through imported Google review text (no JOIN; avoids duplicates).
                Restaurant.google_reviews.any(GoogleReview.review_text.ilike(pattern)),
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
            review_stats_subquery.c.average_rating >= minimum_rating
        )

    return query


def _apply_restaurant_list_sorting(
    query: Any,
    review_stats_subquery: Subquery,
    sort: Literal["name", "rating", "created_at"],
) -> Any:
    if sort == "name":
        return query.order_by(Restaurant.name.asc(), Restaurant.created_at.desc())

    if sort == "rating":
        return query.order_by(
            review_stats_subquery.c.average_rating.desc().nullslast(),
            Restaurant.created_at.desc(),
        )

    return query.order_by(Restaurant.created_at.desc())


def _serialize_restaurant_list_item(
    restaurant: Restaurant,
    average_rating: Optional[float],
    review_count: int,
) -> RestaurantResponse:
    rating = round(average_rating, 1) if average_rating is not None else None
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
            "rating": rating,
            "review_count": review_count,
            "category": restaurant.category,
            "price_level": restaurant.price_level,
            "opening_hours": restaurant.opening_hours,
            "operating_hours": restaurant.operating_hours,
            "thumbnail": restaurant.thumbnail,
            "google_place_id": restaurant.google_place_id,
            "serpapi_data_id": restaurant.serpapi_data_id,
            "reviews_link": restaurant.reviews_link,
            "photos_link": restaurant.photos_link,
            "user_review": restaurant.user_review,
            "average_rating": rating,
            "created_at": restaurant.created_at,
            "updated_at": restaurant.updated_at,
        }
    )


@router.get(
    "",
    response_model=RestaurantListResponse,
    summary="List restaurants",
    description="Retrieve a paginated list of restaurants with optional search, filtering, and sorting.",
    response_description="A paginated list of restaurants.",
    responses={
        200: {"description": "Restaurants retrieved successfully."},
        422: {"description": "Invalid query parameter values."},
    },
)
def list_restaurants(
    search: Annotated[
        Optional[str],
        Query(
            description="Search by restaurant name, city, district, category, description, menu item name, or review text (TasteMap + Google)"
        ),
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
) -> RestaurantListResponse:
    """
    List restaurants with optional search, filters, sorting, and pagination
    (public endpoint).

    - **search**: Case-insensitive search on restaurant name, city, district, category, description, menu item name, and review text (TasteMap + Google).
    - **city**: Filter restaurants located in the given city.
    - **district**: Filter restaurants located in the given district.
    - **category**: Filter restaurants that have at least one menu item in this category.
    - **minimum_rating**: Filter restaurants whose average review rating is at least this value.
    - **sort**: Sort by `name`, `rating`, or `created_at`.
    - **limit / offset**: Pagination controls.
    """
    review_stats_subquery = _build_review_stats_subquery()
    average_rating_column = review_stats_subquery.c.average_rating.label("average_rating")
    review_count_column = func.coalesce(review_stats_subquery.c.review_count, 0).label(
        "review_count"
    )
    restaurant_query = (
        select(Restaurant, average_rating_column, review_count_column)
        .outerjoin(
            review_stats_subquery,
            review_stats_subquery.c.restaurant_id == Restaurant.id,
        )
    )

    restaurant_query = _apply_restaurant_list_filters(
        restaurant_query,
        review_stats_subquery,
        search,
        city,
        district,
        category,
        minimum_rating,
    )
    restaurant_query = _apply_restaurant_list_sorting(
        restaurant_query,
        review_stats_subquery,
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
        _serialize_restaurant_list_item(restaurant, average_rating, review_count)
        for restaurant, average_rating, review_count in rows
    ]

    return RestaurantListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{restaurant_id}",
    response_model=RestaurantDetailResponse,
    summary="Get restaurant details",
    description="Retrieve detailed information for a single restaurant, including menu items and reviews.",
    response_description="Detailed restaurant information.",
    responses={
        200: {"description": "Restaurant details retrieved successfully."},
        404: {"description": "Restaurant not found."},
        422: {"description": "Invalid restaurant identifier."},
    },
)
def get_restaurant_detail(
    restaurant_id: Annotated[
        uuid.UUID,
        Path(description="Unique identifier of the restaurant to retrieve."),
    ],
    db: Session = Depends(get_db),
) -> RestaurantDetailResponse:
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
            selectinload(Restaurant.google_reviews),
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

    tastemap_reviews = restaurant.reviews
    google_reviews = restaurant.google_reviews

    combined_review_count = len(google_reviews) + len(tastemap_reviews)

    rated_values = [
        rating
        for rating in ([r.rating for r in google_reviews] + [r.rating for r in tastemap_reviews])
        if rating is not None
    ]
    combined_average_rating = (
        round(sum(rated_values) / len(rated_values), 1) if rated_values else None
    )

    combined_items: list[tuple[datetime | None, dict[str, Any]]] = []

    for google_review in google_reviews:
        sort_dt = _parse_iso_datetime(google_review.review_date)
        payload = google_review_to_review_response_payload(
            google_review=google_review,
            restaurant_id=restaurant.id,
        )
        combined_items.append((sort_dt, payload))

    for review in tastemap_reviews:
        combined_items.append(
            (
                review.created_at,
                {
                    "id": review.id,
                    "user_id": review.user_id,
                    "rating": review.rating,
                    "comment": review.comment,
                    "created_at": review.created_at,
                    "updated_at": review.updated_at,
                    "author_name": None,
                    "profile_photo": None,
                    "likes": None,
                    "source": "user",
                },
            )
        )

    combined_items.sort(
        key=lambda item: (
            item[0] is None,
            -(item[0].timestamp() if item[0] is not None else 0.0),
        )
    )
    combined_reviews = [payload for _, payload in combined_items]

    return RestaurantDetailResponse.model_validate(
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
            "rating": combined_average_rating,
            "category": restaurant.category,
            "price_level": restaurant.price_level,
            "opening_hours": restaurant.opening_hours,
            "operating_hours": restaurant.operating_hours,
            "thumbnail": restaurant.thumbnail,
            "google_place_id": restaurant.google_place_id,
            "serpapi_data_id": restaurant.serpapi_data_id,
            "reviews_link": restaurant.reviews_link,
            "photos_link": restaurant.photos_link,
            "user_review": restaurant.user_review,
            "created_at": restaurant.created_at,
            "updated_at": restaurant.updated_at,
            "average_rating": combined_average_rating,
            "review_count": combined_review_count,
            "menu_items": list(restaurant.menu_items),
            "reviews": combined_reviews,
        }
    )


@router.post(
    "/{restaurant_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a restaurant review",
    description="Create a TasteMap user review for a restaurant as the currently authenticated user.",
    response_description="The newly created review.",
    responses={
        201: {"description": "Review created successfully."},
        401: {"description": "Authentication required."},
        404: {"description": "Restaurant not found."},
        409: {"description": "The user already reviewed this restaurant."},
        422: {"description": "Validation error in the submitted payload."},
    },
)
def create_restaurant_review(
    restaurant_id: Annotated[
        uuid.UUID,
        Path(description="Unique identifier of the restaurant being reviewed."),
    ],
    data: RestaurantReviewCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Review:
    restaurant_exists = db.execute(
        select(Restaurant.id).where(Restaurant.id == restaurant_id)
    ).scalar_one_or_none()
    if restaurant_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    duplicate = db.execute(
        select(Review.id).where(
            Review.user_id == current_user.id,
            Review.restaurant_id == restaurant_id,
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this restaurant",
        )

    review = Review(
        restaurant_id=restaurant_id,
        user_id=current_user.id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a restaurant",
    description="Create a new restaurant. This endpoint requires admin privileges.",
    response_description="The newly created restaurant.",
    responses={
        201: {"description": "Restaurant created successfully."},
        401: {"description": "Authentication required."},
        403: {"description": "Admin privileges are required."},
        422: {"description": "Validation error in the submitted payload."},
    },
)
def create_restaurant(
    data: RestaurantCreate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
) -> Restaurant:
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


@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Update a restaurant",
    description="Update an existing restaurant. This endpoint requires admin privileges.",
    response_description="The updated restaurant.",
    responses={
        200: {"description": "Restaurant updated successfully."},
        401: {"description": "Authentication required."},
        403: {"description": "Admin privileges are required."},
        404: {"description": "Restaurant not found."},
        422: {"description": "Validation error in the request."},
    },
)
def update_restaurant(
    restaurant_id: Annotated[
        uuid.UUID,
        Path(description="Unique identifier of the restaurant to update."),
    ],
    data: RestaurantUpdate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
) -> Restaurant:
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


@router.delete(
    "/{restaurant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a restaurant",
    description="Delete an existing restaurant. This endpoint requires admin privileges.",
    response_description="Restaurant deleted successfully.",
    responses={
        204: {"description": "Restaurant deleted successfully."},
        401: {"description": "Authentication required."},
        403: {"description": "Admin privileges are required."},
        404: {"description": "Restaurant not found."},
        422: {"description": "Invalid restaurant identifier."},
    },
)
def delete_restaurant(
    restaurant_id: Annotated[
        uuid.UUID,
        Path(description="Unique identifier of the restaurant to delete."),
    ],
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
) -> Response:
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
