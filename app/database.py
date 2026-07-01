import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

# Read DATABASE_URL from .env
# Expected format: postgresql://user:password@localhost:5432/dbname
# We convert it to the async driver format automatically
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in your .env file")

# SQLAlchemy needs asyncpg driver for async Postgres
# Convert: postgresql://... → postgresql+asyncpg://...
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNC_DATABASE_URL = DATABASE_URL
else:
    raise ValueError("DATABASE_URL must start with postgresql://")

# Create the async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,       # Set to True if you want to see SQL queries printed (useful for debugging)
    pool_pre_ping=True  # Automatically reconnects if a DB connection drops
)

# Session factory — use this to get a DB session in your routes
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False  # Keeps objects accessible after commit, important in async context
)

# Base class all your models will inherit from
class Base(DeclarativeBase):
    pass

# Dependency for FastAPI routes — yields a session, closes it after the request
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Call this once at app startup to create all tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)