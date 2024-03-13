import pytest
from httpx import AsyncClient
from env import ROOT
from api.auth import decode_jwt
import random
from test_utils import is_recent_time


@pytest.mark.anyio
async def test_auth(client: AsyncClient):  # nosec
    response = await client.post("auth/login", json={"org": ROOT, "user": ROOT, "passwd": ROOT})
    assert response.status_code == 200
    token = response.json()['token']
    result = decode_jwt(token)
    assert result['org'] == result['name'] == ROOT
    assert result['role'] == ROOT
    
    response = (await client.get(f"auth/permission/{ROOT}/{ROOT}")).json()
    assert response['role'] == ROOT
    assert all(response.values())  # all True