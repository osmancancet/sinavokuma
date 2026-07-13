from collections.abc import AsyncGenerator

from sinavokuma_shared.db import make_engine, make_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

engine = make_engine(settings.database_url)
AsyncSessionLocal = make_session_factory(engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
