from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# =========================
# Database URL
# =========================
DATABASE_URL = "sqlite+aiosqlite:///./database.db"

# =========================
# Engine
# =========================
engine = create_async_engine(
    DATABASE_URL,
    echo=False
)

# =========================
# Base Model
# =========================
Base = declarative_base()

# =========================
# Session Maker
# =========================
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# =========================
# DB Dependency
# =========================
async def get_db():
    async with SessionLocal() as db:
        yield db

# =========================
# Init DB (CREATE TABLES)
# =========================
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
