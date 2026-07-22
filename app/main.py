from fastapi import FastAPI

from app.api.routes import auth, health
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(auth.router)
