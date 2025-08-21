import logging
from datetime import datetime

from sqlalchemy import extract, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from weather_analytics_api.db import Base, async_session, engine

from .models import Weather, WeatherStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def compute_weather_stats(session: AsyncSession = None):
    """
    Compute weather statistics asynchronously.

    For every year, for every weather station, calculate:
    - Average maximum temperature (in degrees Celsius)
    - Average minimum temperature (in degrees Celsius)
    - Total accumulated precipitation (in centimeters)

    Ignores missing data (NULL values) when calculating statistics.
    Uses NULL for statistics that cannot be calculated.
    Handles duplicates gracefully - can be run multiple times.
    """
    local_session = session or async_session()
    start_time = datetime.now()
    logger.info("Starting weather statistics calculation...")

    try:
        # Ensure WeatherStats table exists
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with local_session as session_ctx:
            # Query aggregated stats grouped by station and year
            # SQL aggregate functions automatically ignore NULL values
            query = (
                select(
                    Weather.station_id,
                    extract("year", Weather.date).label("year"),
                    func.avg(Weather.max_temp).label("avg_max_temp"),
                    func.avg(Weather.min_temp).label("avg_min_temp"),
                    func.sum(Weather.precipitation).label("total_precipitation"),
                    func.count().label("total_records"),
                    func.count(Weather.max_temp).label("max_temp_records"),
                    func.count(Weather.min_temp).label("min_temp_records"),
                    func.count(Weather.precipitation).label("precip_records"),
                )
                .group_by(Weather.station_id, extract("year", Weather.date))
                .order_by(Weather.station_id, extract("year", Weather.date))
            )

            result = await session_ctx.execute(query)
            rows = result.all()

            total_stats = 0

            logger.info(f"Found {len(rows)} station-year combinations to process")

            # Process each station-year combination
            for i, row in enumerate(rows, 1):
                try:
                    station_id = row.station_id
                    year = int(row.year)

                    # Handle cases where all values are NULL (no valid data)
                    avg_max_temp = (
                        row.avg_max_temp if row.max_temp_records > 0 else None
                    )
                    avg_min_temp = (
                        row.avg_min_temp if row.min_temp_records > 0 else None
                    )
                    total_precipitation = (
                        row.total_precipitation if row.precip_records > 0 else None
                    )

                    # Use upsert to handle duplicates gracefully
                    stmt = insert(WeatherStats).values(
                        station_id=station_id,
                        year=year,
                        avg_max_temp=avg_max_temp,
                        avg_min_temp=avg_min_temp,
                        total_precipitation=total_precipitation,
                    )

                    # Handle duplicates by updating existing records
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["station_id", "year"],
                        set_=dict(
                            avg_max_temp=stmt.excluded.avg_max_temp,
                            avg_min_temp=stmt.excluded.avg_min_temp,
                            total_precipitation=stmt.excluded.total_precipitation,
                        ),
                    )

                    result = await session_ctx.execute(stmt)

                    # Check if this was an insert or update
                    if result.rowcount > 0:
                        # SQLite doesn't distinguish between insert/update in rowcount
                        # So we count all as processed
                        total_stats += 1

                    # Log progress every 50 records
                    if i % 50 == 0:
                        logger.info(f"Processed {i}/{len(rows)} statistics records...")

                except Exception as e:
                    logger.error(
                        f"Error processing stats for {row.station_id} year {row.year}: {e}"
                    )
                    continue

            # Commit all changes
            await session_ctx.commit()

            duration = datetime.now() - start_time
            logger.info(f"Statistics calculation complete in {duration}")
            logger.info(f"Processed {total_stats} station-year combinations")

            return total_stats

    except Exception as e:
        logger.error(f"Error during statistics calculation: {e}")
        if not session:  # Only rollback if we created the session
            async with local_session as session_ctx:
                await session_ctx.rollback()
        raise


async def compute_weather_stats_detailed(session: AsyncSession = None):
    """
    Alternative implementation with more detailed logging and error handling.
    Processes statistics with explicit NULL filtering for better control.
    """
    local_session = session or async_session()
    start_time = datetime.now()
    logger.info("Starting detailed weather statistics calculation...")

    try:
        # Ensure WeatherStats table exists
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with local_session as session_ctx:
            # Get all unique station-year combinations first
            station_years_query = (
                select(Weather.station_id, extract("year", Weather.date).label("year"))
                .distinct()
                .order_by(Weather.station_id, extract("year", Weather.date))
            )

            station_years_result = await session_ctx.execute(station_years_query)
            station_years = station_years_result.all()

            total_stats = 0
            logger.info(
                f"Processing {len(station_years)} unique station-year combinations"
            )

            for i, station_year in enumerate(station_years, 1):
                station_id = station_year.station_id
                year = int(station_year.year)

                try:
                    # Calculate avg max temp (ignoring NULL values)
                    max_temp_query = select(func.avg(Weather.max_temp)).where(
                        Weather.station_id == station_id,
                        extract("year", Weather.date) == year,
                        Weather.max_temp.is_not(None),
                    )
                    avg_max_temp = await session_ctx.scalar(max_temp_query)

                    # Calculate avg min temp (ignoring NULL values)
                    min_temp_query = select(func.avg(Weather.min_temp)).where(
                        Weather.station_id == station_id,
                        extract("year", Weather.date) == year,
                        Weather.min_temp.is_not(None),
                    )
                    avg_min_temp = await session_ctx.scalar(min_temp_query)

                    # Calculate total precipitation (ignoring NULL values)
                    precip_query = select(func.sum(Weather.precipitation)).where(
                        Weather.station_id == station_id,
                        extract("year", Weather.date) == year,
                        Weather.precipitation.is_not(None),
                    )
                    total_precipitation = await session_ctx.scalar(precip_query)

                    # Use upsert to handle duplicates
                    stmt = insert(WeatherStats).values(
                        station_id=station_id,
                        year=year,
                        avg_max_temp=avg_max_temp,
                        avg_min_temp=avg_min_temp,
                        total_precipitation=total_precipitation,
                    )

                    stmt = stmt.on_conflict_do_update(
                        index_elements=["station_id", "year"],
                        set_=dict(
                            avg_max_temp=stmt.excluded.avg_max_temp,
                            avg_min_temp=stmt.excluded.avg_min_temp,
                            total_precipitation=stmt.excluded.total_precipitation,
                        ),
                    )

                    await session_ctx.execute(stmt)
                    total_stats += 1

                    # Log progress
                    if i % 25 == 0:
                        logger.info(
                            f"Processed {i}/{len(station_years)} statistics... "
                            f"Current: {station_id} {year}"
                        )

                except Exception as e:
                    logger.error(f"Error processing {station_id} year {year}: {e}")
                    continue

            await session_ctx.commit()

            duration = datetime.now() - start_time
            logger.info(f"Detailed statistics calculation complete in {duration}")
            logger.info(
                f"Successfully processed {total_stats} station-year combinations"
            )

            return total_stats

    except Exception as e:
        logger.error(f"Error during detailed statistics calculation: {e}")
        if not session:  # Only rollback if we created the session
            async with local_session as session_ctx:
                await session_ctx.rollback()
        raise


# For backwards compatibility and easy imports
compute_stats = compute_weather_stats


if __name__ == "__main__":
    import asyncio

    asyncio.run(compute_weather_stats())
