import pytest
from httpx import AsyncClient
from env import ROOT
from database.models import User
import random
from test_utils import is_recent_time

@pytest.mark.anyio
async def test_user(client: AsyncClient):  # nosec
    # root org only
    response = await client.get("orgs")
    assert response.status_code == 200 and response.json() == [{'name': ROOT}]

    response = await client.get(f"users/{ROOT}")
    assert response.status_code == 200
    response = response.json()
    assert len(response) == 1
    response = response[0]
    assert response[User.org.name] == ROOT
    assert response[User.name.name] == ROOT
    assert is_recent_time(response[User.datetime.name])
    response = await client.get(f"users/不存在的org")
    assert response.status_code == 200 and response.json() == []
    
    # create
    usernames = {'test_user', 'User1', 'user2'}
    for user in usernames:
        response = await client.post(f"users/{ROOT}/{user}")
        assert response.status_code == 200
    random_user = random.choice(list(usernames))
    response = await client.post(f"users/{ROOT}/{random_user}")
    assert 400 <= response.status_code < 500 and random_user in response.json()['detail']
    
    # get
    result = (await client.get(f"users/{ROOT}")).json()
    assert len(result) == len(usernames) + 1
    for user in result:
        if user['name'] != ROOT:
            assert user['name'] in usernames
    filter = 'user'
    result = (await client.get(f"users/{ROOT}?filter={filter}")).json()
    for user in result:
        assert filter.lower() in user['name'].lower()
    result = (await client.get(f"users/{ROOT}?filter={filter}&case=1")).json()
    for user in result:
        assert filter in user['name']
    
    assert (await client.get(f"users/不存在的org/{random_user}")).json() is None
    assert (await client.get(f"users/{ROOT}/a")).json() is None
    random_user = random.choice(list(usernames))
    result = (await client.get(f"users/{ROOT}/{random_user}")).json()
    assert result['name'] == random_user
    assert is_recent_time(result['datetime'])
    
    # update
    assert (await client.patch(f"users/{ROOT}/test_user")).status_code >= 400
    await client.patch(f"users/{ROOT}/test_user/userUpdated")
    assert (await client.get(f"users/{ROOT}/test_user")).json() is None
    assert (await client.get(f"users/{ROOT}/userUpdated")).json()['name'] == 'userUpdated'
    assert (await client.patch(f"users/{ROOT}/test_user/userUpdated")).status_code >= 400
    assert (await client.patch(f"users/{ROOT}/User1/userUpdated")).status_code >= 400
    
    # delete
    assert (await client.delete(f"users/{ROOT}/test_org")).status_code >= 400
    assert (await client.delete(f"users/{ROOT}/userUpdated")).status_code == 200
    assert (await client.get(f"users/{ROOT}/userUpdated")).json() is None
