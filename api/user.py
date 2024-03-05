from utils import jsonify
from fastapi import APIRouter, HTTPException
from database.models import User
from database.connection import db
from sqlalchemy import select, func, update, delete
from api.version import API_PREFIX
router = APIRouter(
    prefix= API_PREFIX + '/users',
    tags = ['users']
)

@router.get('/{org}/')
async def get_users(org: str, filter: str = '', case: bool = False):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(User.org, User.name, User.role, User.datetime).filter(User.org == org).filter(User.name.like(f'%{filter}%')))
        else:
            result = await s.execute(select(User.org, User.name, User.role, User.datetime).filter(User.org == org).filter(func.lower(User.name).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/{org}/{name}')
async def get_user(org: str, name: str):
    async with db.create_session_readonly() as s:
        result = await s.execute(select(User.org, User.name, User.role, User.datetime).filter(User.org == org).filter(User.name == name))
        return jsonify(result.one_or_none())

@router.post('/{org}/{name}')
async def create_user(org: str, name: str):
    if not name:
        raise HTTPException(400, f"No {User.__name__} name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.name == name))).one_or_none():
                raise HTTPException(400, f"{User.__name__} {name} already exists")
            s.add(User(name=name, org=org))

@router.patch('/{org}/{name}/{newname}')
async def rename_user(org: str, name: str, newname: str):
    if not name:
        raise HTTPException(400, f"No {User.__name__} name")
    if not newname:
        raise HTTPException(400, f"No {User.__name__} new name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.org == org).filter(User.name == name))).one_or_none() is None:
                raise HTTPException(400, f"{User.__name__} {name} does not exist")
            if (await s.execute(select(User).filter(User.org == org).filter(User.name == newname))).one_or_none():
                raise HTTPException(400, f"{User.__name__} {newname} exists")
            await s.execute(update(User).where(User.name==name).values(name=newname))

# TODO: change user role

@router.delete('/{org}/{name}')
async def delete_user(org: str, name: str):
    if not name:
        raise HTTPException(400, f"No {User.__name__} name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.name == name).filter(User.org == org))).one_or_none() is None:
                raise HTTPException(400, f"{User.__name__} {name} does not exist")
            await s.execute(delete(User).where(User.name==name).filter(User.org == org))
