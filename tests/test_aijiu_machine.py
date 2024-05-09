import datetime

import pytest
from httpx import AsyncClient
from env import ROOT
import random
from database.models import GPSPosition
from database.connection import db
from test_utils import is_recent_time, root_org_only
from utils import datetime_utc_8
import dateutil.parser
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete

@pytest.mark.anyio
async def test_aijiu_machine(client: AsyncClient):  # nosec
    # root org only
    response = await client.get("orgs")
    assert response.status_code == 200
    root_org_only(response.json())

    test_org = "test_org"
    await client.post(f"orgs/{test_org}")
    assert (await client.get(f"machines/orgs/{ROOT}")).json() == []
    assert (await client.get(f"machines/orgs/{test_org}")).json() == []
    
    # create
    machine_ids_in_root = {'test_machine', 'Machine1', 'machine2'}
    for machine in machine_ids_in_root:
        response = await client.post(f"machines/id/{machine}/{ROOT}")
        assert response.status_code == 200
    machine_ids_in_test_org = {'test_machine_in_test_org', 'Machine1_in_test_org', 'machine2_in_test_org'}
    for machine in machine_ids_in_test_org:
        response = await client.post(f"machines/id/{machine}/{test_org}")
        assert response.status_code == 200
    # No duplicate machine id
    for _ in range(5):
        random_machine = random.choice(list(machine_ids_in_root.union(machine_ids_in_test_org)))
        response = await client.post(f"machines/id/{random_machine}/{ROOT}")
        assert 400 <= response.status_code < 500 and random_machine in response.json()['detail']
        response = await client.post(f"machines/id/{random_machine}/{test_org}")
        assert 400 <= response.status_code < 500 and random_machine in response.json()['detail']

    # get
    filter = 'machine'
    
    async def get_machines_in_org():
        result = (await client.get(f"machines/orgs/{ROOT}")).json()
        assert len(result) == len(machine_ids_in_root)
        for machine in result:
            assert machine['id'] in machine_ids_in_root
        result = (await client.get(f"machines/orgs/{ROOT}?filter={filter}")).json()
        for machine in result:
            assert filter.lower() in machine['id'].lower()
        result = (await client.get(f"machines/orgs/{ROOT}?filter={filter}&case=1")).json()
        for machine in result:
            assert filter in machine['id']
    await get_machines_in_org()
    
    async def get_machines():
        result = (await client.get(f"machines")).json()
        assert len(result) == len(machine_ids_in_root.union(machine_ids_in_test_org))
        for machine in result:
            assert machine['id'] in machine_ids_in_root.union(machine_ids_in_test_org)
        result = (await client.get(f"machines?filter={filter}")).json()
        for machine in result:
            assert filter.lower() in machine['id'].lower()
        result = (await client.get(f"machines?filter={filter}&case=1")).json()
        for machine in result:
            assert filter in machine['id']
    await get_machines()
    
    assert (await client.get(f"machines/orgs/不存在的org")).json() == []
    assert (await client.get(f"machines/id/不存在的id")).json() is None
    for _ in range(5):
        random_machine = random.choice(list(machine_ids_in_root.union(machine_ids_in_test_org)))
        result = (await client.get(f"machines/id/{random_machine}")).json()
        assert result['id'] == random_machine
        assert is_recent_time(result['createTime'])
    random_machine = random.choice(list(machine_ids_in_root))
    result = (await client.get(f"machines/orgs/{ROOT}")).json()
    assert random_machine in {i['id'] for i in result }

    # update
    random_machine_in_root = random.choice(list(machine_ids_in_root))
    random_machine_in_test_org = random.choice(list(machine_ids_in_test_org))
    assert (await client.patch(f"machines/id/不存在的machine/org/{test_org}")).status_code >= 400
    assert (await client.patch(f"machines/id/{random_machine_in_root}/不存在的org")).status_code >= 400
    assert (await client.patch(f"machines/id/{random_machine_in_root}/{test_org}")).status_code == 200
    assert random_machine_in_root not in {i['id'] for i in (await client.get(f"machines/orgs/{ROOT}")).json()}
    assert random_machine_in_root in {i['id'] for i in (await client.get(f"machines/orgs/{test_org}")).json()}
    machine_ids_in_root.remove(random_machine_in_root)
    machine_ids_in_test_org.add(random_machine_in_root)
    assert (await client.patch(f"machines/id/{random_machine_in_test_org}/{ROOT}")).status_code == 200
    assert random_machine_in_test_org not in {i['id'] for i in (await client.get(f"machines/orgs/{test_org}")).json()}
    assert random_machine_in_test_org in {i['id'] for i in (await client.get(f"machines/orgs/{ROOT}")).json()}
    machine_ids_in_test_org.remove(random_machine_in_test_org)
    machine_ids_in_root.add(random_machine_in_test_org)

    # gps
    all_machine_ids = [m['id'] for m in (await client.get(f"machines")).json()]
    random.shuffle(all_machine_ids)
    now = datetime_utc_8()
    async with db.create_session() as s:
        for m in all_machine_ids:
            for i in range(1, 5):
                s.add(GPSPosition(client_id=m, timestamp=now + datetime.timedelta(seconds=i), degreeE=-i/10 + hash(m) % -120, degreeN=i/10))
    latest_gps = (await client.get(f"machines/gps")).json()
    for g in latest_gps:
        machine_id, timestamp, degreeE, degreeN, org = g['client_id'], dateutil.parser.isoparse(g['timestamp']), g['degreeE'], g['degreeN'], g['org']
        assert timestamp == now + datetime.timedelta(seconds=4)
        assert degreeE == -4/10 + hash(machine_id) % -120
        assert degreeN == 4/10
        if machine_id in machine_ids_in_root:
            assert org == ROOT
        if machine_id in machine_ids_in_test_org:
            assert org == test_org

    # delete
    random_machine = random.choice(list(machine_ids_in_test_org))
    assert (await client.delete(f"machines/id/不存在的machine")).status_code >= 400
    try:
        await client.delete(f"machines/id/{random_machine}")
    except IntegrityError:
        pass
    else:
        raise IndexError("Deleted a machine with its GPS record stored")
    async with db.create_session() as s:
        await s.execute(delete(GPSPosition))
    assert (await client.delete(f"machines/id/{random_machine}")).status_code == 200
    assert random_machine not in {i['id'] for i in (await client.get(f"machines/orgs/{test_org}")).json()}
