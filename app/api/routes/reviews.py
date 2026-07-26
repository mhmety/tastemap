
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new review for a restaurant by a user.

    - **restaurant_id**: UUID of the restaurant being reviewed. Must exist.
    - **user_id**: UUID of the user writing the review. Must exist.
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

    user_exists = db.execute(
        select(User).where(User.id == data.user_id)
    ).scalar_one_or_none()

    if user_exists is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not exist",
        )

    duplicate = db.execute(
        select(Review).where(
            Review.user_id == data.user_id,
            Review.restaurant_id == data.restaurant_id,
        )
    ).scalar_one_or_none()

    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already reviewed this restaurant",
        )

    review = Review(
        restaurant_id=data.restaurant_id,
        user_id=data.user_id,
        rating=data.rating,
        comment=data.comment,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve a single review by its UUID.

    - **review_id**: UUID of the review to fetch.
    """
    query = select(Review).where(Review.id == review_id)
    result = db.execute(query)
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return review


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: uuid.UUID,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing review.

    Only the rating and/or comment may be updated. Fields that are
    not provided in the request body remain unchanged.

    - **review_id**: UUID of the review to update.
    """
    query = select(Review).where(Review.id == review_id)
    result = db.execute(query)
    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)

    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Delete a review.

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

    db.delete(review)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
