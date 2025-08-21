import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from weather_analytics_api.db import Base
from weather_analytics_api.ingest import ingest_data

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_ingest_file(test_session, tmp_path):
    # Create a temporary directory and a sample station file
    station_file = tmp_path / "STATION1.txt"
    station_file.write_text("20250101\t100\t50\t0\n" "20250102\t200\t100\t5\n")

    # Call ingest_data with the temp directory
    await ingest_data(str(tmp_path), session=test_session)

    # Verify rows were inserted
    result = await test_session.execute(text("SELECT COUNT(*) FROM weather"))
    count = result.scalar()
    assert count == 2  # matches rows in sample file
