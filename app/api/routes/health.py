from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Return the operational health status and service metadata for the TasteMap API.",
    response_description="Service health information.",
    responses={
        200: {
            "description": "Service is healthy.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "TasteMap API",
                        "version": "1.0.0",
                        "timestamp": "2026-07-27T10:00:00Z",
                    }
                }
            },
        }
    },
)
def health_check() -> dict[str, str]:
    """Return application health status."""
    return {
        "status": "healthy",
        "service": "TasteMap API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
