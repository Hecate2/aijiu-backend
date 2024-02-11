from utils import jsonify
from fastapi import APIRouter, HTTPException
from models import User, db
from sqlalchemy import select, func, update, delete
from api.version import API_PREFIX
router = APIRouter(
    prefix= API_PREFIX + '/org',
    tags = ['users']
)

@router.get('/')
async def get_users(filter: str = '', case: bool = False):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(User.name).filter(User.name.like(f'%{filter}%')))
        else:
            result = await s.execute(select(User.name).filter(func.lower(User.name).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/{name}')
async def get_user(name: str = ''):
    async with db.create_session_readonly() as s:
        result = await s.execute(select(User.name, User.datetime).filter(User.name == name))
        return jsonify(result.one_or_none())

@router.post('/{name}')
async def create_user(name: str):
    if not name:
        raise HTTPException(400, f"No {User.__name__} name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.name == name))).one_or_none():
                raise HTTPException(400, f"{User.__name__} {name} already exists")
            s.add(User(name=name))

@router.patch('/{name}/{newname}')
async def rename_user(name: str, newname: str):
    if not name:
        raise HTTPException(400, f"No {User.__name__} name")
    if not newname:
        raise HTTPException(400, f"No {User.__name__} new name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.name == name))).one_or_none() is None:
                raise HTTPException(400, f"{User.__name__} {name} does not exist")
            await s.execute(update(User).where(User.name==name).values(name=newname))

@router.delete('/{name}')
async def delete_user(name: str):
    if not name:
        raise HTTPException(400, f"No {User.__name__} name")
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.name == name))).one_or_none() is None:
                raise HTTPException(400, f"{User.__name__} {name} does not exist")
            await s.execute(delete(User).where(User.name==name))
