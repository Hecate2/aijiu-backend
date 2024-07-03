from utils import jsonify
from fastapi import APIRouter, HTTPException, Depends
from api.auth import JWTBearer
from database.models import User, BackendPermissionByRole
from database.connection import db
from sqlalchemy import select, func, update, delete
from api.version import API_PREFIX
from database.models import ORG_ADMIN, ORG_USER, ROOT
from api.auth import allow
router = APIRouter(
    prefix= API_PREFIX + '/users',
    tags = ['users']
)

@router.get('/{org}')
@allow({BackendPermissionByRole.read_my_org_user}, super_permissions={BackendPermissionByRole.super_read,BackendPermissionByRole.super_write})
async def get_users(org: str, filter: str = '', case: bool = False, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(User.org, User.name, User.role, User.createTime).filter(User.org == org).filter(User.name.like(f'%{filter}%')))
        else:
            result = await s.execute(select(User.org, User.name, User.role, User.createTime).filter(User.org == org).filter(func.lower(User.name).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/{org}/{name}')
@allow({BackendPermissionByRole.read_my_org_user}, super_permissions={BackendPermissionByRole.super_read})
async def get_user(org: str, name: str, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        result = await s.execute(select(User.org, User.name, User.role, User.createTime).filter(User.org == org).filter(User.name == name))
        return jsonify(result.one_or_none())

@router.post('/{org}/{name}')
@allow({BackendPermissionByRole.write_my_org_user}, super_permissions={BackendPermissionByRole.super_read})
async def create_user(org: str, name: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.org == org).filter(User.name == name))).one_or_none():
                raise HTTPException(400, f"{User.__name__} {name} already exists")
            s.add(User(name=name, org=org))

@router.patch('/{org}/{username}/role/{new_role}')
@allow({BackendPermissionByRole.write_my_org_user})
async def change_user_role(org: str, username: str, new_role: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            user = (await s.execute(select(User).filter(User.org == org).filter(User.name == username))).one_or_none()
            if not user:
                raise HTTPException(400, f"{User.__name__} {username} does not exist")
            await s.execute(update(User).filter(User.org == org).where(User.name == username).values(role=new_role))
            

@router.patch('/{org}/{name}/{newname}')
@allow({BackendPermissionByRole.write_my_org_user})
async def rename_user(org: str, name: str, newname: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.org == org).filter(User.name == name))).one_or_none() is None:
                raise HTTPException(400, f"{User.__name__} {name} does not exist")
            if (await s.execute(select(User).filter(User.org == org).filter(User.name == newname))).one_or_none():
                raise HTTPException(400, f"{User.__name__} {newname} exists")
            await s.execute(update(User).filter(User.org == org).where(User.name==name).values(name=newname))

@router.delete('/{org}/{name}')
@allow({BackendPermissionByRole.write_my_org_user}, allow_self=False)
async def delete_user(org: str, name: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(User).filter(User.org == org).filter(User.name == name))).one_or_none() is None:
                raise HTTPException(400, f"{User.__name__} {name} does not exist")
            await s.execute(delete(User).filter(User.org == org).where(User.name==name).filter(User.org == org))
