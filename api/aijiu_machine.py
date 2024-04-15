from typing import Union, Dict
from utils import jsonify
from fastapi import APIRouter, HTTPException
from database.models import AijiuMachine, Org
from database.connection import db
from sqlalchemy import select, func, update, delete
from api.version import API_PREFIX
from env import EMQX_HTTP_CLIENT, is_prod_env
router = APIRouter(
    prefix= API_PREFIX + '/machines',
    tags = ['machines']
)

@router.get('/')
async def get_machines(filter: str = '', case: bool = False):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.org, AijiuMachine.createTime).filter(AijiuMachine.id.like(f'%{filter}%')))
        else:
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.org, AijiuMachine.createTime).filter(func.lower(AijiuMachine.id).like(func.lower(f'%{filter}%'))))
        result = jsonify(result.all())
        connected = await get_machines_online()
        for c in result:
            if c['id'] in connected:
                c['connectedAt'] = connected[c['id']]
        return result

@router.get('/orgs/{org}/')
async def get_machines_in_org(org: str, filter: str = '', case: bool = False):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.createTime).filter(AijiuMachine.org == org).filter(AijiuMachine.id.like(f'%{filter}%')))
        else:
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.createTime).filter(AijiuMachine.org == org).filter(func.lower(AijiuMachine.id).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/online')
async def get_machines_online() -> Dict[str, str]:
    '''
    
    :return: clientid: connect_time '2024-04-15T13:01:50.655+08:00'
    '''
    page = 1
    all_data = dict()
    if not is_prod_env():
        return all_data
    while True:
        result = (await EMQX_HTTP_CLIENT.get(f'/clients?limit=1000&conn_state=connected&page={page}')).json()
        for c in result['data']:
            all_data[c['clientid']] = c['connected_at']
        if not result['meta']['hasnext']:
            return all_data
        page += 1

@router.get('/id/{id}/')
async def get_machine_by_id(id: str):
    async with db.create_session_readonly() as s:
        result = await s.execute(select(AijiuMachine.org, AijiuMachine.id, AijiuMachine.createTime).filter(AijiuMachine.id == id))
        return jsonify(result.one_or_none())

@router.post('/id/{id}/{org}/')
async def create_machine_for_org(id: str, org: Union[str, None]):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(AijiuMachine).filter(AijiuMachine.id == id))).one_or_none():
                raise HTTPException(400, f"{AijiuMachine.__name__} {id} already exists")
            if org and (await s.execute(select(Org).filter(Org.name == org))).one_or_none() is None:
                raise HTTPException(400, f"{Org.__name__} {org} does not exist")
            s.add(AijiuMachine(id=id, org=org))

@router.patch('/id/{id}/{neworg}/')
async def change_machine_org(id: str, neworg: str):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(AijiuMachine).filter(AijiuMachine.id == id))).one_or_none() is None:
                raise HTTPException(400, f"{AijiuMachine.__name__} {id} does not exist")
            if neworg and (await s.execute(select(Org).filter(Org.name == neworg))).one_or_none() is None:
                raise HTTPException(400, f"{Org.__name__} {neworg} does not exist")
            await s.execute(update(AijiuMachine).where(AijiuMachine.id==id).values(org=neworg))

@router.delete('/id/{id}/')
async def delete_machine(id: str):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(AijiuMachine).filter(AijiuMachine.id == id))).one_or_none() is None:
                raise HTTPException(400, f"{AijiuMachine.__name__} {id} does not exist")
            await s.execute(delete(AijiuMachine).where(AijiuMachine.id == id))
