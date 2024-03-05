from typing import Union
from utils import jsonify
from fastapi import APIRouter, HTTPException
from database.models import AijiuMachine, Org
from database.connection import db
from sqlalchemy import select, func, update, delete
from api.version import API_PREFIX
router = APIRouter(
    prefix= API_PREFIX + '/machines',
    tags = ['machines']
)

@router.get('/')
async def get_machines(filter: str = '', case: bool = False):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.org, AijiuMachine.datetime).filter(AijiuMachine.id.like(f'%{filter}%')))
        else:
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.org, AijiuMachine.datetime).filter(func.lower(AijiuMachine.id).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/orgs/{org}/')
async def get_machines_in_org(org: str, filter: str = '', case: bool = False):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.datetime).filter(AijiuMachine.org == org).filter(AijiuMachine.id.like(f'%{filter}%')))
        else:
            result = await s.execute(select(AijiuMachine.id, AijiuMachine.datetime).filter(AijiuMachine.org == org).filter(func.lower(AijiuMachine.id).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/id/{id}/')
async def get_machine_by_id(id: str):
    async with db.create_session_readonly() as s:
        result = await s.execute(select(AijiuMachine.org, AijiuMachine.id, AijiuMachine.datetime).filter(AijiuMachine.id == id))
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
async def update_machine_org(id: str, neworg: str):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(AijiuMachine).filter(AijiuMachine.id == id))).one_or_none() is None:
                raise HTTPException(400, f"{AijiuMachine.__name__} {id} does not exist")
            if neworg and (await s.execute(select(Org).filter(Org.name == neworg))).one_or_none() is None:
                raise HTTPException(400, f"{Org.__name__} {neworg} does not exist")
            await s.execute(update(AijiuMachine).where(AijiuMachine.id==id).values(org=neworg))

@router.delete('/id/{id}/')
async def delete_machine(id: str):
    if not id:
        raise HTTPException(400, f"No {AijiuMachine.__name__} name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(AijiuMachine).filter(AijiuMachine.id == id))).one_or_none() is None:
                raise HTTPException(400, f"{AijiuMachine.__name__} {id} does not exist")
            await s.execute(delete(AijiuMachine).where(AijiuMachine.id == id))
