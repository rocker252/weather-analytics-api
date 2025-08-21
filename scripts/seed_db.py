import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from weather_analytics_api.db import async_session, init_db
from weather_analytics_api.models import Weather, WeatherStats


async def seed_data():
    # Initialize DB tables
    await init_db()

    async with async_session() as session:
        # Check if the Weather table already has data for our test station
        result = await session.execute(select(Weather).where(Weather.station_id == "USC00110072"))
        if result.scalars().first():
            print("Data already exists, skipping seed.")
            return

        # Seed Weather table
        weather_records = [
            Weather(station_id="STATION1", date=date(2025, 8, 19), max_temp=35.0, min_temp=25.0, precipitation=10.0),
            Weather(station_id="STATION2", date=date(2025, 8, 19), max_temp=30.0, min_temp=20.0, precipitation=5.0),
            Weather(station_id="USC00110072", date=date(2025, 8, 19), max_temp=32.0, min_temp=22.0, precipitation=8.0),
        ]
        session.add_all(weather_records)

        # Seed WeatherStats table
        stats_records = [
            WeatherStats(station_id="STATION1", year=2025, avg_max_temp=35.0, avg_min_temp=25.0, total_precipitation=10.0),
            WeatherStats(station_id="STATION2", year=2025, avg_max_temp=30.0, avg_min_temp=20.0, total_precipitation=5.0),
            WeatherStats(station_id="USC00110072", year=2025, avg_max_temp=32.0, avg_min_temp=22.0, total_precipitation=8.0),
        ]
        session.add_all(stats_records)

        await session.commit()
        print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_data())
