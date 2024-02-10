from typing import List
from utils import jsonify
from fastapi import APIRouter, HTTPException
from models import Org, ClientId, AijiuUser, db
from sqlalchemy import select, func

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
async def create_org(name: str = ''):
    async with db.create_session() as s:
        if (await s.execute(select(Org).filter(Org.name == name))).one_or_none():
            raise HTTPException(400, {"success": False, "message": f"{Org.__name__} {name} already exists"})
        s.add(Org(name=name))
    return {"success": True}
