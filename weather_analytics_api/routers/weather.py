import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from weather_analytics_api.auth import verify_token
from weather_analytics_api.db import get_db
from weather_analytics_api.models import Weather, WeatherStats
from weather_analytics_api.schemas import (
    PaginatedResponse,
    PaginationInfo,
    WeatherOut,
    WeatherStatsOut,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# HTTPBearer scheme for optional authentication
bearer_scheme = HTTPBearer()


# JWT verification dependency (optional - for enhanced security)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """Optional authentication - remove if not needed for assignment."""
    token = credentials.credentials
    username = verify_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return username


@router.get("/", response_model=PaginatedResponse[WeatherOut])
async def get_weather(
    date: Optional[str] = None,  # Single date as per assignment specs
    station_id: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # current_user: str = Depends(get_current_user),  # Uncomment to enable auth
):
    """
    Retrieve weather measurements with filtering and pagination.

    - **date**: Filter by specific date (YYYY-MM-DD format)
    - **station_id**: Filter by weather station ID
    - **page**: Page number for pagination (default: 1)
    - **limit**: Number of records per page (default: 100, max: 1000)
    """
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

    try:
        # Build base query
        query = select(Weather)

        # Apply filters
        if station_id:
            query = query.where(Weather.station_id == station_id)

        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                query = query.where(Weather.date == date_obj)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
                )

        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Calculate pagination
        pages = (total + limit - 1) // limit if total > 0 else 0
        offset = (page - 1) * limit

        # Apply pagination and ordering
        query = (
            query.order_by(Weather.station_id, Weather.date).limit(limit).offset(offset)
        )

        # Execute query
        result = await db.execute(query)
        rows = result.scalars().all()

        # Convert to response format
        weather_data = []
        for w in rows:
            weather_data.append(
                WeatherOut(
                    station_id=w.station_id,
                    date=w.date.strftime("%Y-%m-%d"),
                    max_temp=w.max_temp,
                    min_temp=w.min_temp,
                    precipitation=w.precipitation,  # Already in centimeters from ingest
                )
            )

        return PaginatedResponse(
            data=weather_data,
            pagination=PaginationInfo(page=page, limit=limit, total=total, pages=pages),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_weather: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=PaginatedResponse[WeatherStatsOut])
async def get_weather_stats(
    year: Optional[int] = None,
    station_id: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # current_user: str = Depends(get_current_user),  # Uncomment to enable auth
):
    """
    Retrieve weather statistics with filtering and pagination.

    - **year**: Filter by specific year
    - **station_id**: Filter by weather station ID
    - **page**: Page number for pagination (default: 1)
    - **limit**: Number of records per page (default: 100, max: 1000)
    """
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

    # Validate year if provided
    if year is not None and (year < 1900 or year > 2100):
        raise HTTPException(
            status_code=400, detail="Year must be between 1900 and 2100"
        )

    try:
        # Build base query
        query = select(WeatherStats)

        # Apply filters
        if station_id:
            query = query.where(WeatherStats.station_id == station_id)

        if year:
            query = query.where(WeatherStats.year == year)

        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Calculate pagination
        pages = (total + limit - 1) // limit if total > 0 else 0
        offset = (page - 1) * limit

        # Apply pagination and ordering
        query = (
            query.order_by(WeatherStats.station_id, WeatherStats.year)
            .limit(limit)
            .offset(offset)
        )

        # Execute query
        result = await db.execute(query)
        rows = result.scalars().all()

        # Convert to response format
        stats_data = []
        for s in rows:
            stats_data.append(
                WeatherStatsOut(
                    station_id=s.station_id,
                    year=s.year,
                    avg_max_temp=s.avg_max_temp,
                    avg_min_temp=s.avg_min_temp,
                    total_precipitation=s.total_precipitation,  # Already in centimeters
                )
            )

        return PaginatedResponse(
            data=stats_data,
            pagination=PaginationInfo(page=page, limit=limit, total=total, pages=pages),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_weather_stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
