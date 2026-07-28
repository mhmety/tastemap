
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.favorite import Favorite
from app.models.restaurant import Restaurant
from app.schemas.favorite import FavoriteCreate, FavoriteResponse

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post(
    "",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a favorite",
    description="Add a restaurant to the authenticated user's favorites.",
    response_description="The newly created favorite entry.",
    responses={
        201: {
            "description": "Favorite created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": "9c3a2222-aaaa-4f52-bbbb-1234567890ab",
                        "user_id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
                        "restaurant_id": "4b4733c3-1136-4105-a957-dd4ed1cab0e2",
                        "created_at": "2026-07-27T10:00:00Z",
                    }
                }
            },
        },
        400: {
            "description": "Restaurant does not exist or is already favorited.",
            "content": {
                "application/json": {
                    "example": {"detail": "Restaurant is already in your favorites"}
                }
            },
        },
        401: {"description": "Authentication required."},
        422: {"description": "Validation error in the submitted payload."},
    },
)
def create_favorite(
    data: FavoriteCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Favorite:
    """
    Add a restaurant to the currently authenticated user's favorites.

    The owner is determined from the JWT token; the client cannot submit a
    user_id in the request body.

    - **restaurant_id**: UUID of the restaurant to favorite. Must exist.

    Attempting to favorite the same restaurant twice returns HTTP 400.
    """
    restaurant_exists = db.execute(
        select(Restaurant).where(Restaurant.id == data.restaurant_id)
    ).scalar_one_or_none()

    if restaurant_exists is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant does not exist",
        )

    existing = db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.restaurant_id == data.restaurant_id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant is already in your favorites",
        )

    favorite = Favorite(
        user_id=current_user.id,
        restaurant_id=data.restaurant_id,
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


@router.get(
    "/me",
    response_model=List[FavoriteResponse],
    summary="List my favorites",
    description="Retrieve the authenticated user's favorite restaurants.",
    response_description="A list of favorite entries for the current user.",
    responses={
        200: {"description": "Favorites retrieved successfully."},
        401: {"description": "Authentication required."},
    },
)
def list_my_favorites(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> List[Favorite]:
    """
    List the currently authenticated user's favorite restaurants.

    Requires authentication.
    """
    query = select(Favorite).where(Favorite.user_id == current_user.id)
    result = db.execute(query)
    favorites = result.scalars().all()
    return list(favorites)


@router.delete(
    "/{favorite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a favorite",
    description="Remove a favorite entry owned by the current user, or by an admin.",
    response_description="Favorite deleted successfully.",
    responses={
        204: {"description": "Favorite deleted successfully."},
        401: {"description": "Authentication required."},
        403: {"description": "The current user is not allowed to delete this favorite."},
        404: {"description": "Favorite not found."},
        422: {"description": "Invalid favorite identifier."},
    },
)
def delete_favorite(
    favorite_id: Annotated[
        uuid.UUID,
        Path(description="Unique identifier of the favorite entry to delete."),
    ],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    """
    Remove a restaurant from the authenticated user's favorites by favorite ID.

    Only the owner of the favorite or an admin may remove it.

    - **favorite_id**: UUID of the favorite entry to remove.
    """
    query = select(Favorite).where(Favorite.id == favorite_id)
    result = db.execute(query)
    favorite = result.scalar_one_or_none()

    if favorite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )

    if favorite.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to remove this favorite",
        )

    db.delete(favorite)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
