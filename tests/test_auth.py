import pytest
from httpx import AsyncClient
from env import ROOT
import random
from test_utils import is_recent_time


@pytest.mark.anyio
async def test_auth(client: AsyncClient):  # nosec
    response = await client.post("auth/login", json={"username": ROOT, "passwd": ROOT})
    assert response.status_code == 200 and response.json() == {"success": True}
    
    response = (await client.get(f"auth/permission/{ROOT}/{ROOT}")).json()
    assert response['role'] == ROOT
    assert all(response.values())  # all True