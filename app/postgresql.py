from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.settings import settings

database_url = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_DB_PORT}/{settings.POSTGRES_DB}"
)

engine = create_async_engine(database_url, echo=False)

async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
