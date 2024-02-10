import datetime

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from main import app
from models import Org, init_tables, drop_tables
import random
from dateutil import parser
import datetime


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as c:
            yield c


@pytest.mark.anyio
async def test_create_user(client: AsyncClient):  # nosec
    await drop_tables()
    await init_tables()
    response = await client.get("/api/v1/orgs")
    assert response.status_code == 200 and response.json() == []
    response = await client.get("/api/v1/orgs/a")
    assert response.status_code == 200 and response.text == 'null' and response.json() == None
    
    org_names = {'test_org', 'Hospital1', 'hospital2'}
    for org in org_names:
        response = await client.post(f"/api/v1/orgs/{org}")
        assert response.status_code == 200, response.json() == {'success': True}
    
    result = (await client.get("/api/v1/orgs")).json()
    assert len(result) == len(org_names)
    for org in result:
        assert org['name'] in org_names
    filter = 'Hospital'
    result = (await client.get(f"/api/v1/orgs?filter={filter}")).json()
    for org in result:
        assert filter.lower() in org['name'].lower()
    result = (await client.get(f"/api/v1/orgs?filter={filter}&case=1")).json()
    for org in result:
        assert filter in org['name']

    result = (await client.get("/api/v1/orgs/a")).json()
    assert result is None
    random_org = random.choice(list(org_names))
    result = (await client.get(f"/api/v1/orgs/{random_org}")).json()
    assert (result['name'] == random_org
        and abs(parser.parse(result['datetime']) - datetime.datetime.utcnow()).total_seconds()
            - datetime.timedelta(hours=8).total_seconds()) < 10