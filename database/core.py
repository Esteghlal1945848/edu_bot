from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession
)

from sqlalchemy.orm import (
    sessionmaker,
    declarative_base
)

DATABASE_URL = "sqlite+aiosqlite:///database.db"

engine = create_async_engine(
    DATABASE_URL
)

Base = declarative_base()

SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():

    async with SessionLocal() as db:
        yield db
