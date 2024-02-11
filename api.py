from typing import List
from utils import jsonify
from fastapi import APIRouter, HTTPException
from models import Org, ClientId, db
from sqlalchemy import select, func, update, delete

API_PREFIX = '/api/v1'
router = APIRouter(
    prefix= API_PREFIX,
    tags = ['main']
)

@router.get('/')
async def root():
    return {"api/v1": "艾灸后端API/v1"}

@router.get('/orgs')
async def get_orgs(filter: str = '', case: bool = False):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(Org.name).filter(Org.name.like(f'%{filter}%')))
        else:
            result = await s.execute(select(Org.name).filter(func.lower(Org.name).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/orgs/{name}')
async def get_org(name: str = ''):
    async with db.create_session_readonly() as s:
        result = await s.execute(select(Org.name, Org.datetime).filter(Org.name == name))
        return jsonify(result.one_or_none())

@router.post('/orgs/{name}')
async def create_org(name: str):
    if not name:
        raise HTTPException(400, f"No {Org.__name__} name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(Org).filter(Org.name == name))).one_or_none():
                raise HTTPException(400, f"{Org.__name__} {name} already exists")
            s.add(Org(name=name))

@router.put('/orgs/{name}/{newname}')
async def rename_org(name: str, newname: str):
    if not name:
        raise HTTPException(400, f"No {Org.__name__} name")
    if not newname:
        raise HTTPException(400, f"No {Org.__name__} new name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(Org).filter(Org.name == name))).one_or_none() is None:
                raise HTTPException(400, f"{Org.__name__} {name} does not exist")
            await s.execute(update(Org).where(Org.name==name).values(name=newname))

@router.delete('/orgs/{name}')
async def delete_org(name: str):
    if not name:
        raise HTTPException(400, f"No {Org.__name__} name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(Org).filter(Org.name == name))).one_or_none() is None:
                raise HTTPException(400, f"{Org.__name__} {name} does not exist")
            await s.execute(delete(Org).where(Org.name==name))
