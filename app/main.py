from fastapi import FastAPI

from app.api.routes import auth, favorites, health, restaurants, reviews

openapi_tags = [
    {
        "name": "auth",
        "description": "User registration and JWT-based authentication endpoints.",
    },
    {
        "name": "restaurants",
        "description": "Restaurant discovery, search, detail, and admin management endpoints.",
    },
    {
        "name": "reviews",
        "description": "Review creation, retrieval, update, and deletion endpoints.",
    },
    {
        "name": "favorites",
        "description": "Authenticated user endpoints for managing favorite restaurants.",
    },
    {
        "name": "health",
        "description": "Operational health and service availability endpoints.",
    },
]

app = FastAPI(
    title="TasteMap API",
    summary="Restaurant discovery platform with JWT authentication and personalized food discovery features.",
    description=(
        "TasteMap REST API for discovering restaurants and dishes, managing reviews and favorites, "
        "and administering restaurant data.\n\n"
        "Key features include:\n"
        "- JWT authentication\n"
        "- Restaurant search, filtering, and pagination\n"
        "- Review and favorite management\n"
        "- Admin-only restaurant management\n"
        "- Health monitoring endpoints"
    ),
    version="1.0.0",
    contact={
        "name": "Mehmet Yildiz",
        "email": "mehmet@example.com",
    },
    license_info={
        "name": "MIT",
        "identifier": "MIT",
    },
    openapi_tags=openapi_tags,
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
