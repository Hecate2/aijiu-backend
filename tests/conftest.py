import sys
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from main import app
from database.connection import init_tables, drop_tables, drop_database
from env import ROOT
import pytest

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test/api/v1/", follow_redirects=True) as c:
            token = (await c.post("auth/login", json={"org": ROOT, "user": ROOT, "passwd": ROOT})).json()['token']
            c.headers['Authorization'] = f'Bearer {token}'
            yield c


@pytest.fixture(scope="session", autouse=True)
async def execute_before_any_test():
    await drop_tables()
    await init_tables()

@pytest.hookimpl(tryfirst=True)
def pytest_exception_interact(call):
    raise call.excinfo.value

@pytest.hookimpl(tryfirst=True)
def pytest_internalerror(excinfo):
    raise excinfo.value