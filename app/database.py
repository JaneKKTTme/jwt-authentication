from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings


DATABASE_URL = settings.database_url
engine = create_async_engine(DATABASE_URL, echo=True)

AsyncLocalSession = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

async def init_db():
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
	async with AsyncLocalSession() as session:
		try:
			yield session
		finally:
			await session.close()

