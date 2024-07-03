import datetime
from typing import Union, Dict
import asyncio
from utils import jsonify, datetime_utc_8
from fastapi import APIRouter, HTTPException, Depends
from database.models import AijiuMachine, Org, BackendPermissionByRole
from database.models import AitiaoPasswd, AitiaoLife, AijiuStartEnd, AijiuTemperature, CatalystTemperature, FanRpm, GPSPosition
from database.connection import db
from sqlalchemy import select, func, update, delete
from api.version import API_PREFIX
from api.auth import allow, JWTBearer
from env import EMQX_HTTP_CLIENT, is_prod_env
router = APIRouter(
    prefix= API_PREFIX + '/machines',
    tags = ['machines']
)

@router.get('')
@allow({}, super_permissions={BackendPermissionByRole.super_read})
async def get_machines(filter: str = '', case: bool = False, auth = Depends(JWTBearer())):
    connected = asyncio.create_task(get_machines_online())
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.org, AijiuMachine.model, AijiuMachine.remark, AijiuMachine.createTime).filter(AijiuMachine.id.like(f'%{filter}%')))
        else:
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.org, AijiuMachine.model, AijiuMachine.remark, AijiuMachine.createTime).filter(func.lower(AijiuMachine.id).like(func.lower(f'%{filter}%'))))
    result = jsonify(result.all())
    # connected = await get_machines_online()
    connected = await connected
    for c in result:
        if c['id'] in connected:
            c['connectedAt'] = connected[c['id']]
        # else:
        #     c['connectedAt'] = '1970-01-01T00:00:00.000+00:00'
    return result

@router.get('/gps')
@allow({}, super_permissions={BackendPermissionByRole.super_read})
async def get_machines_by_gps(auth = Depends(JWTBearer())):
# async def get_machines_by_gps():
    """
    :return: distinct GPSPosition records of different client_ids, picking only the latest record
    """
    async with db.create_session_readonly() as s:
        subquery = select(
            GPSPosition,
            AijiuMachine.org,
            func.rank().over(
                order_by=GPSPosition.timestamp.desc(),
                partition_by=GPSPosition.client_id
            ).label('rank'),
        ).join(AijiuMachine).subquery()
        result = await s.execute(select(*([*subquery.columns][:-1])).filter(subquery.c.rank == 1))
    return jsonify(result.all())

@router.get('/orgs/{org}')
@allow({BackendPermissionByRole.read_my_org_aijiu_client}, super_permissions={BackendPermissionByRole.super_read})
async def get_machines_in_org(org: str, filter: str = '', case: bool = False, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.createTime, AijiuMachine.model, AijiuMachine.remark).filter(AijiuMachine.org == org).filter(AijiuMachine.id.like(f'%{filter}%')))
        else:
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.createTime, AijiuMachine.model, AijiuMachine.remark).filter(AijiuMachine.org == org).filter(func.lower(AijiuMachine.id).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/online')
# @allow({}, super_permissions={BackendPermissionByRole.super_read})
async def get_machines_online(auth = Depends(JWTBearer())) -> Dict[str, str]:
    '''
    
    :return: clientid: connect_time '2024-04-15T13:01:50.655+08:00'
    '''
    page = 1
    all_data = dict()
    if not is_prod_env():
        return all_data
    while True:
        result = await EMQX_HTTP_CLIENT.get(f'/clients?limit=1000&conn_state=connected&page={page}')
        result = result.json()
        for c in result['data']:
            all_data[c['clientid']] = c['connected_at']
        if not result['meta']['hasnext']:
            return all_data
        page += 1

@router.get('/id/{id}')
async def get_machine_by_id(id: str, days: int = 100, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        machine = jsonify((await s.execute(select(
            AijiuMachine.org, AijiuMachine.id, AijiuMachine.createTime, AijiuMachine.model, AijiuMachine.remark
        ).filter(AijiuMachine.id == id))).one_or_none())
        if not machine:
            return machine
        fan_rpm = jsonify((await s.execute(
            select(FanRpm.rpm, FanRpm.timestamp)
            .filter(FanRpm.client_id == id)
            .filter(FanRpm.timestamp >= datetime_utc_8() - datetime.timedelta(days=days)))).all())
        catalyst_temperature = jsonify((await s.execute(
            select(CatalystTemperature.temperature, CatalystTemperature.timestamp)
            .filter(CatalystTemperature.client_id == id)
            .filter(CatalystTemperature.timestamp >= datetime_utc_8() - datetime.timedelta(days=days)))).all())
        aitiao_life = jsonify((await s.execute(
            select(AitiaoLife.aitiao_life, AitiaoLife.timestamp)
            .filter(AitiaoLife.client_id == id)
            .filter(AitiaoLife.timestamp >= datetime_utc_8() - datetime.timedelta(days=days)))).all())
        aijiu_temperature = jsonify((await s.execute(
            select(AijiuTemperature.temperature, AijiuTemperature.timestamp)
            .filter(AijiuTemperature.client_id == id)
            .filter(AijiuTemperature.timestamp >= datetime_utc_8() - datetime.timedelta(days=days)))).all())
        machine['fanRpm'] = fan_rpm
        machine['catalystTemperature'] = catalyst_temperature
        machine['aitiaoLife'] = aitiao_life
        machine['aijiuTemperature'] = aijiu_temperature
        return machine

@router.post('/id/{id}/{org}')
@allow({BackendPermissionByRole.write_my_org_aijiu_client})
async def create_machine_for_org(id: str, org: Union[str, None], auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(AijiuMachine).filter(AijiuMachine.id == id))).one_or_none():
                raise HTTPException(400, f"{AijiuMachine.__name__} {id} already exists")
            if org and (await s.execute(select(Org).filter(Org.name == org))).one_or_none() is None:
                raise HTTPException(400, f"{Org.__name__} {org} does not exist")
            s.add(AijiuMachine(id=id, org=org))

@router.patch('/remark/{id}/{remark}')
async def set_machine_remark(id: str, remark: str, auth = Depends(JWTBearer())):
    if not remark: remark = None
    async with db.create_session() as s:
        await s.execute(update(AijiuMachine).where(AijiuMachine.id==id).values(remark=remark))

@router.patch('/model/{id}/{model}')
async def set_machine_model(id: str, model: str, auth = Depends(JWTBearer())):
    if not model: model = None
    async with db.create_session() as s:
        await s.execute(update(AijiuMachine).where(AijiuMachine.id==id).values(model=model))

@router.patch('/id/{id}/{neworg}')
async def change_machine_org(id: str, neworg: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(AijiuMachine).filter(AijiuMachine.id == id))).one_or_none() is None:
                raise HTTPException(400, f"{AijiuMachine.__name__} {id} does not exist")
            if neworg and (await s.execute(select(Org).filter(Org.name == neworg))).one_or_none() is None:
                raise HTTPException(400, f"{Org.__name__} {neworg} does not exist")
            await s.execute(update(AijiuMachine).where(AijiuMachine.id==id).values(org=neworg))

@router.delete('/id/{id}')
@allow({BackendPermissionByRole.write_my_org_aijiu_client})
async def delete_machine(id: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(AijiuMachine).filter(AijiuMachine.id == id))).one_or_none() is None:
                raise HTTPException(400, f"{AijiuMachine.__name__} {id} does not exist")
            await s.execute(delete(AijiuMachine).where(AijiuMachine.id == id))
