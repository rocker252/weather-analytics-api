import os

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL from environment or fallback to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Async session factory
async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI endpoints
async def get_db():
    async with async_session() as session:
        yield session


# Initialize database tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# For sync operations (like ingest_data)
sync_engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./test.db"), echo=True)
SessionLocal = sessionmaker(bind=sync_engine)
