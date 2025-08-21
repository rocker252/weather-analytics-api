from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from weather_analytics_api.analyze import compute_weather_stats
from weather_analytics_api.db import Base
from weather_analytics_api.models import Weather, WeatherStats

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_session():
    # Create async engine and session
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_compute_weather_stats(test_session):
    # Insert sample weather data
    sample_data = [
        Weather(
            station_id="ST1",
            date=date(2025, 1, 1),
            max_temp=10,
            min_temp=5,
            precipitation=0,
        ),
        Weather(
            station_id="ST1",
            date=date(2025, 1, 2),
            max_temp=20,
            min_temp=10,
            precipitation=5,
        ),
        Weather(
            station_id="ST2",
            date=date(2025, 1, 1),
            max_temp=15,
            min_temp=7,
            precipitation=2,
        ),
    ]

    async with test_session.begin():
        test_session.add_all(sample_data)

    # Run async stats computation
    await compute_weather_stats(test_session)

    # Verify results
    result = await test_session.execute(
        select(WeatherStats).order_by(WeatherStats.station_id)
    )
    stats = result.scalars().all()

    assert len(stats) == 2  # 2 stations
    assert stats[0].station_id == "ST1"
    assert stats[0].avg_max_temp == 15  # (10+20)/2
    assert stats[0].avg_min_temp == 7.5
    assert stats[0].total_precipitation == 5
    assert stats[1].station_id == "ST2"
    assert stats[1].avg_max_temp == 15
    assert stats[1].avg_min_temp == 7
    assert stats[1].total_precipitation == 2
