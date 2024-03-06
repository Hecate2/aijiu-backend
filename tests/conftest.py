from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from main import app
from database.connection import init_tables, drop_tables, drop_database
import pytest

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test/api/v1/", follow_redirects=True) as c:
            yield c


@pytest.fixture(scope="session", autouse=True)
async def execute_before_any_test():
    await drop_tables()
    await init_tables()
