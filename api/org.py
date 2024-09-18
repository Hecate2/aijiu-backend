from utils import jsonify
from fastapi import APIRouter, HTTPException, Depends
from api.auth import JWTBearer
from database.models import Org, ParentOrg, User, BackendPermissionByRole
from database.connection import db
from sqlalchemy import select, func, update, delete
from api.version import API_PREFIX
from api.auth import allow
from env import ROOT
router = APIRouter(
    prefix= API_PREFIX + '/orgs',
    tags = ['orgs']
)

@router.get('')
@allow({})  # super permission
async def get_orgs(filter: str = '', case: bool = False, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        if case:  # case sensitive
            result = await s.execute(select(Org.name, Org.createTime, Org.authLevel).filter(Org.name.like(f'%{filter}%')))
        else:
            result = await s.execute(select(Org.name, Org.createTime, Org.authLevel).filter(func.lower(Org.name).like(func.lower(f'%{filter}%'))))
        return jsonify(result.all())

@router.get('/{name}')
async def get_org(name: str, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        result = await s.execute(select(Org.name, Org.createTime, Org.authLevel).filter(Org.name == name))
        return jsonify(result.one_or_none())

@router.get('/children/{name}')
async def get_children_orgs(name: str, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        return jsonify((await s.execute(select(ParentOrg.org).filter(ParentOrg.parentOrg == name))).all())

@router.get('/parent/{name}')
async def get_parent_org(name: str, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        return jsonify((await s.execute(select(ParentOrg.parentOrg).filter(ParentOrg.org == name))).one_or_none())

@router.get('/{org_name}/usercount')
async def get_org_user_count(org_name: str, auth = Depends(JWTBearer())):
    async with db.create_session_readonly() as s:
        return await s.scalar(select(func.count()).select_from(select(User).filter(User.org == org_name).subquery()))

@router.post('/{name}')
async def create_org(name: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(Org).filter(Org.name == name))).one_or_none():
                raise HTTPException(400, f"{Org.__name__} {name} already exists")
            s.add(Org(name=name, authLevel=1))
            # TODO: decide authLevel and parent org

@router.post('/{name}/{newname}')
async def rename_org(name: str, newname: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (org := (await s.execute(select(Org.authLevel).filter(Org.name == name))).one_or_none()) is None:
                raise HTTPException(400, f"{Org.__name__} {name} does not exist")
            if org.authLevel == 0:
                raise HTTPException(400, f"Cannot rename root org `{name}`")
            if (await s.execute(select(Org).filter(Org.name == newname))).one_or_none():
                raise HTTPException(400, f"{Org.__name__} {newname} exists")
            await s.execute(update(Org).where(Org.name==name).values(name=newname))

@router.delete('/{name}')
async def delete_org(name: str, auth = Depends(JWTBearer())):
    async with db.create_session() as s:
        async with s.begin():
            if (org := (await s.execute(select(Org.authLevel).filter(Org.name == name))).one_or_none()) is None:
                return
            if org.authLevel == 0:
                raise HTTPException(400, f"Cannot delete root org `{name}`")
            if user_count := await get_org_user_count(name) > 0:
                raise HTTPException(400, f"Cannot delete {Org.__name__} {name} because it has {user_count} users. Delete all of its users first.")
            await s.execute(delete(Org).where(Org.name==name))
