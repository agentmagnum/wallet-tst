import os
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


PROJECT_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/wallet_db",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.db.models import Wallet
from app.db.session import get_db_session
from app.main import app


engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
SessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def override_get_db_session():
    async with SessionFactory() as session:
        yield session


app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    config = Config(str(PROJECT_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(config, "head")
    yield


@pytest_asyncio.fixture(autouse=True)
async def clear_wallets_table(migrated_database):
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE wallets"))
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as api_client:
        yield api_client


@pytest_asyncio.fixture
async def db_session():
    async with SessionFactory() as session:
        yield session


@pytest_asyncio.fixture
async def wallet_factory(db_session: AsyncSession):
    async def create_wallet(balance: Decimal = Decimal("0.00")) -> uuid.UUID:
        wallet = Wallet(balance=balance)
        db_session.add(wallet)
        await db_session.commit()
        return wallet.id

    return create_wallet


@pytest.fixture(scope="session", autouse=True)
def dispose_engine(request):
    def finalizer():
        import asyncio

        asyncio.run(engine.dispose())

    request.addfinalizer(finalizer)
