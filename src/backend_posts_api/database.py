import random
from collections.abc import AsyncGenerator

from faker import Faker
from faker.providers import internet, lorem, person
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import Post, User
from .settings import settings

DATABASE_URL = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.posts_db_name}"
engine = None


async def _create_data(engine: AsyncEngine):
    fake = Faker(["en_US"])
    fake.add_provider(person)
    fake.add_provider(internet)
    fake.add_provider(lorem)
    n_users = 5
    user_ids = list(range(1, n_users + 1))
    users = [User(name=fake.name(), email=fake.email()) for _ in range(n_users)]
    posts = [
        Post(
            title=fake.text(50),
            content=fake.paragraph(4),
            user_id=random.choice(user_ids),
        )
        for _ in range(50)
    ]
    async with AsyncSession(engine) as session:
        for user in users:
            session.add(user)
        await session.commit()
        for post in posts:
            session.add(post)
        await session.commit()


async def init_db(
    create_data: bool = False,
) -> None:
    """Initialize the database and optionally fill it with sample data.

    :params:
    create_data: bool, optional
    If True, create sample data in the database.
    """
    global engine
    logger.info("Creating database connection with {}", DATABASE_URL)
    engine = create_async_engine(DATABASE_URL, echo=True, future=True)
    async with engine.begin() as conn:
        try:
            await conn.run_sync(SQLModel.metadata.drop_all)
        except:  # noqa: E722
            # If this fails because the table doesn't exist, keep going
            pass
        await conn.run_sync(SQLModel.metadata.create_all)
    if create_data:
        await _create_data(engine)


async def get_session() -> AsyncGenerator[AsyncSession, None, None]:
    """Yield a session object to work with the database."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
