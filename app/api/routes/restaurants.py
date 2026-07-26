
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantResponse

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
