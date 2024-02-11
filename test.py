import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from main import app
from models import Org, init_tables, drop_tables, ROOT
import random
from dateutil import parser
import datetime


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test/api/v1/", follow_redirects=True) as c:
            yield c


@pytest.mark.anyio
async def test_org(client: AsyncClient):  # nosec
    await drop_tables()
    await init_tables()
    # root org only
    response = await client.get("orgs")
    assert response.status_code == 200 and response.json() == [{'name': ROOT}]
    response = await client.get("orgs/a")
    assert response.status_code == 200 and response.text == 'null' and response.json() == None
    
    # create
    org_names = {'test_org', 'Hospital1', 'hospital2'}
    for org in org_names:
        response = await client.post(f"orgs/{org}")
        assert response.status_code == 200
    random_org = random.choice(list(org_names))
    response = await client.post(f"orgs/{random_org}")
    assert 400 <= response.status_code < 500 and random_org in response.json()['detail']

    # get
    result = (await client.get("orgs")).json()
    assert len(result) == len(org_names) + 1
    for org in result:
        if org['name'] != ROOT:
            assert org['name'] in org_names
    filter = 'Hospital'
    result = (await client.get(f"orgs?filter={filter}")).json()
    for org in result:
        assert filter.lower() in org['name'].lower()
    result = (await client.get(f"orgs?filter={filter}&case=1")).json()
    for org in result:
        assert filter in org['name']

    result = (await client.get("orgs/a")).json()
    assert result is None
    random_org = random.choice(list(org_names))
    result = (await client.get(f"orgs/{random_org}")).json()
    assert (result['name'] == random_org
        and abs(parser.parse(result['datetime']) - datetime.datetime.utcnow()).total_seconds()
            - datetime.timedelta(hours=8).total_seconds()) < 10
    
    # update
    assert (await client.patch("orgs/test_org")).status_code >= 400
    await client.patch("orgs/test_org/hospitalUpdated")
    assert (await client.get("orgs/test_org")).json() is None
    assert (await client.get("orgs/hospitalUpdated")).json()['name'] == 'hospitalUpdated'
    assert (await client.patch("orgs/test_org/hospitalUpdated")).status_code >= 400
    
    # delete
    assert (await client.delete("orgs/test_org")).status_code >= 400
    await client.delete("orgs/hospitalUpdated")
    assert (await client.get("orgs/hospitalUpdated")).json() is None