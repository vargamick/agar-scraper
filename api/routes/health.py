"""
Health check routes.

Provides endpoints for monitoring API and database health.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.config import settings
from api.dependencies import get_session
from api.schemas.common import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_session)):
    """
    Health check endpoint.

    Returns:
        Health status including API version and database connectivity
    """
    # Check database connection
    database_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = "disconnected"

    return HealthResponse(
        status="healthy" if database_status == "connected" else "unhealthy",
        version=settings.APP_VERSION,
        database=database_status,
    )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint.

    Returns:
        Pong response
    """
    return {"message": "pong"}
