
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review",
    description="Create a review for a restaurant as the currently authenticated user.",
    response_description="The newly created review.",
    responses={
        201: {
            "description": "Review created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": "33333333-3333-3333-3333-333333333333",
                        "restaurant_id": "4b4733c3-1136-4105-a957-dd4ed1cab0e2",
                        "user_id": "f2dcda87-75f7-450d-8e29-1f201cd48658",
                        "rating": 5,
                        "comment": "Excellent burgers and quick service.",
                        "created_at": "2026-07-27T10:00:00Z",
                        "updated_at": "2026-07-27T10:00:00Z",
                    }
                }
            },
        },
        400: {
            "description": "Restaurant does not exist or the user already reviewed it.",
            "content": {
                "application/json": {
                    "example": {"detail": "You have already reviewed this restaurant"}
                }
            },
        },
        401: {"description": "Authentication required."},
        422: {"description": "Validation error in the submitted payload."},
    },
)
def create_review(
    data: ReviewCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Review:
    """
    Create a new review for a restaurant as the currently authenticated user.

    Requires a valid logged-in user. The review's author is automatically set
    to the JWT-authorized user; the client cannot submit a user_id in the
    request body.

    - **restaurant_id**: UUID of the restaurant being reviewed. Must exist.
    - **rating**: Integer rating from 1 to 5 (inclusive).
    - **comment**: Optional text comment (max 1000 characters).

    A user may only review a specific restaurant once. Attempting to
    create a duplicate review for the same (user, restaurant) pair
    returns HTTP 400.
    """
    restaurant_exists = db.execute(
        select(Restaurant).where(Restaurant.id == data.restaurant_id)
    ).scalar_one_or_none()

    if restaurant_exists is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant does not exist",
        )

    duplicate = db.execute(
        select(Review).where(
            Review.user_id == current_user.id,
            Review.restaurant_id == data.restaurant_id,
        )
    ).scalar_one_or_none()

    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this restaurant",
        )

    review = Review(
        restaurant_id=data.restaurant_id,
        user_id=current_user.id,
        rating=data.rating,
        comment=data.comment,
    )

    db.add(review)
    db.commit()
    db.refresh(review)
    review.user = current_user

    return review


@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Get a review",
    description="Retrieve a single review by its UUID.",
    response_description="The requested review.",
    responses={
        200: {"description": "Review retrieved successfully."},
        404: {"description": "Review not found."},
        422: {"description": "Invalid review identifier."},
    },
)
def get_review(
    review_id: Annotated[
        uuid.UUID,
        Path(description="Unique identifier of the review to retrieve."),
    ],
    db: Session = Depends(get_db),
) -> Review:
    """
    Retrieve a single review by its UUID (public, no authentication required).

    - **review_id**: UUID of the review to fetch.
    """
    from sqlalchemy.orm import selectinload

    query = select(Review).options(selectinload(Review.user)).where(Review.id == review_id)
    result = db.execute(query)
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return review


@router.put(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Update a review",
    description="Update a review owned by the current user, or by an admin.",
    response_description="The updated review.",
    responses={
        200: {"description": "Review updated successfully."},
        401: {"description": "Authentication required."},
        403: {"description": "The current user is not allowed to update this review."},
        404: {"description": "Review not found."},
        422: {"description": "Validation error in the request."},
    },
)
@router.patch(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Patch a review",
    description="Partially update a review owned by the current user, or by an admin.",
    response_description="The updated review.",
    include_in_schema=False,
)
def update_review(
    review_id: Annotated[
        uuid.UUID,
        Path(description="Unique identifier of the review to update."),
    ],
    data: ReviewUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Review:
    """
    Update an existing review.

    Only the original review author OR an admin may update a review.
    Only the rating and/or comment may be updated. Fields that are not
    provided in the request body remain unchanged.

    - **review_id**: UUID of the review to update.
    """
    from sqlalchemy.orm import selectinload

    query = select(Review).options(selectinload(Review.user)).where(Review.id == review_id)
    result = db.execute(query)
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    if review.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this review",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)
    if not review.user:
        review.user = current_user

    return review


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a review",
    description="Delete a review owned by the current user, or by an admin.",
    response_description="Review deleted successfully.",
    responses={
        204: {"description": "Review deleted successfully."},
        401: {"description": "Authentication required."},
        403: {"description": "The current user is not allowed to delete this review."},
        404: {"description": "Review not found."},
        422: {"description": "Invalid review identifier."},
    },
)
def delete_review(
    review_id: Annotated[
        uuid.UUID,
        Path(description="Unique identifier of the review to delete."),
    ],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    """
    Delete a review.

    Only the original review author OR an admin may delete a review.

    - **review_id**: UUID of the review to delete.
    """
    query = select(Review).where(Review.id == review_id)
    result = db.execute(query)
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    if review.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this review",
        )

    db.delete(review)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

