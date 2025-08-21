import asyncio
import logging
import os
import sys
import zipfile
from datetime import datetime
from io import BytesIO

import aiofiles
import aiohttp
from sqlalchemy.dialects.sqlite import insert

from weather_analytics_api.db import Base, async_session, engine

from .models import Weather

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_URL = (
    "https://github.com/corteva/code-challenge-template/archive/refs/heads/main.zip"
)


async def download_and_extract(data_dir="wx_data"):
    """Download and extract wx_data asynchronously if not found locally."""
    logger.info(f"{data_dir} not found. Downloading from GitHub...")

    async with aiohttp.ClientSession() as session:
        async with session.get(DATA_URL) as response:
            response.raise_for_status()
            content = await response.read()

    with zipfile.ZipFile(BytesIO(content)) as zf:
        root_dir = zf.namelist()[0]
        wx_data_path = f"{root_dir}wx_data/"
        zf.extractall()
        os.rename(wx_data_path, data_dir)

    logger.info(f"Downloaded and extracted {data_dir}.")


def parse_line(line: str):
    """Parse a single line of weather data."""
    try:
        parts = line.strip().split("\t")
        if len(parts) != 4:
            raise ValueError(f"Expected 4 fields, got {len(parts)}")

        date_str, max_t, min_t, prcp = parts
        date = datetime.strptime(date_str, "%Y%m%d").date()
        max_temp = None if int(max_t) == -9999 else int(max_t) / 10.0
        min_temp = None if int(min_t) == -9999 else int(min_t) / 10.0
        precipitation = None if int(prcp) == -9999 else int(prcp) / 100.0
        return date, max_temp, min_temp, precipitation
    except (ValueError, IndexError) as e:
        logger.warning(f"Skipping malformed line: {line.strip()}: {e}")
        return None


async def ingest_data(data_dir="wx_data", session=None):
    """Ingest weather data using provided async session."""
    local_session = session or async_session()

    # Ensure tables are created asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    total = 0
    duplicates = 0
    skipped = 0
    start = datetime.now()

    if not os.path.exists(data_dir):
        await download_and_extract(data_dir)

    logger.info(f"Starting ingestion from {data_dir}...")

    async with local_session as session_ctx:
        files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
        logger.info(f"Found {len(files)} files to process")

        for i, filename in enumerate(files, 1):
            station_id = os.path.splitext(filename)[0]
            path = os.path.join(data_dir, filename)
            file_records = 0
            file_duplicates = 0

            logger.info(
                f"Processing file {i}/{len(files)}: {filename} for station {station_id}"
            )

            try:
                async with aiofiles.open(path, mode="r") as f:
                    async for line in f:
                        parsed = parse_line(line)
                        if parsed is None:
                            skipped += 1
                            continue

                        date, mx, mn, pr = parsed

                        # Use upsert to handle duplicates gracefully
                        stmt = insert(Weather).values(
                            station_id=station_id,
                            date=date,
                            max_temp=mx,
                            min_temp=mn,
                            precipitation=pr,
                        )

                        # Handle duplicates by doing nothing (ignore)
                        stmt = stmt.on_conflict_do_nothing(
                            index_elements=["station_id", "date"]
                        )

                        result = await session_ctx.execute(stmt)

                        # Check if row was actually inserted
                        if result.rowcount > 0:
                            file_records += 1
                            total += 1
                        else:
                            file_duplicates += 1
                            duplicates += 1

                # Commit after each file
                await session_ctx.commit()
                logger.info(
                    f"Completed {filename}: {file_records} new records, {file_duplicates} duplicates"
                )

            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
                await session_ctx.rollback()
                continue

    duration = datetime.now() - start
    logger.info(f"Ingestion complete in {duration}")
    logger.info(
        f"Total: {total} new records, {duplicates} duplicates, {skipped} malformed lines"
    )


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "wx_data"
    asyncio.run(ingest_data(data_dir))
