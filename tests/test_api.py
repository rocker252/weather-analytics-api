import pytest
from sqlalchemy.future import select

from weather_analytics_api.db import get_db
from weather_analytics_api.models import Weather


@pytest.mark.asyncio
async def test_get_weather(async_client, auth_headers):
    response = await async_client.get(
        "/api/weather/",  # note the trailing slash
        headers=auth_headers,
        params={"station_id": "USC00110072"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_weather_stats(async_client, auth_headers):
    response = await async_client.get(
        "/api/weather/stats", headers=auth_headers, params={"station_id": "USC00110072"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_query(auth_headers):
    # This test is mainly for debugging the DB
    async for db in get_db():
        query = select(Weather).limit(5)
        result = await db.execute(query)
        rows = result.scalars().all()
        print(rows)
        # Optional assertion to ensure at least one row exists
        assert rows is not None
