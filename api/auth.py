import os
from functools import wraps
from hashlib import sha512
from typing import Dict, Union, Iterable
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body, HTTPException
from api.version import API_PREFIX
from database.models import User, ParentOrg, BackendPermissionByRole
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import InstrumentedAttribute
from database.connection import db
from utils import jsonify, datetime_utc_8
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from env import is_prod_env

SECRET_KEY = "艾灸后端foobar阿巴阿巴"
SECRET_KEY_PATH = './cryptography/aijiu_secret_key.txt'
# if is_prod_env() and not os.path.isfile(SECRET_KEY_PATH):
#     raise FileNotFoundError(f'为了安全，必须设定{SECRET_KEY_PATH}')
if os.path.isfile(SECRET_KEY_PATH):
    with open(SECRET_KEY_PATH, 'r') as f:
        SECRET_KEY = sha512(f.read().strip().encode('utf-8')).hexdigest()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
REFRESH_TOKEN_EXPIRE_MINUTES = 120


def encode_jwt(original_data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    now = datetime_utc_8()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {  # iss，nbf等key是jwt保留字段
        'iss': '艾灸后端',
        'nbf': int(now.timestamp()),
        'iat': int(now.timestamp()),
        'exp': int(expire.timestamp()),
        # 'aud': '艾灸后端用户',
    }
    for k, v in original_data.items():
        payload[k] = v  # 可能会覆盖iss，nbf这些字段，但这是故意的feature，不是bug
        # 其实也可以用payload的内容写入original_data，但这会改变外部输入的original_data
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_jwt(encoded_jwt: str) -> dict: return jwt.decode(encoded_jwt, SECRET_KEY, algorithms=ALGORITHM)
# except JWTError?

router = APIRouter(
    prefix= API_PREFIX + '/auth',
    tags = ['auth']
)

@router.post('/login')
async def login(org: str = Body(), user: str = Body(), passwd = Body()):
    async with db.create_session_readonly() as s:
        userObj = (await s.execute(select(User.org, User.name, User.role, User.passwd).filter(User.org == org).filter(User.name == user))).one_or_none()
    if not userObj:
        raise HTTPException(403, f"No user {user} in org {org}")
    if userObj.passwd == None or userObj.passwd == passwd or userObj.passwd == sha512((passwd + SECRET_KEY).encode('utf-8')).digest():
        return {"token": encode_jwt({
            User.org.name: userObj.org,
            User.name.name: userObj.name,
            User.role.name: userObj.role,
        })}
    raise HTTPException(403, f"Incorrect passwd for user {user} in org {org}")

# TODO: change passwd

@router.get('/permission/{org}/{username}')
async def get_permission(org: str, username: str):
    async with db.create_session_readonly() as s:
        async with s.begin():
            role = (await s.execute(select(User.role).filter(User.org == org).filter(User.name == username))).one()[0]
            permission = (await s.execute(select(*BackendPermissionByRole.__table__.columns).filter_by(role=role))).one()
            return jsonify(permission)

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = False):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code. Try login again.")
        if not credentials.scheme == "Bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme. Try login again.")
        if not (payload := self.verify_jwt(credentials.credentials)):
            raise HTTPException(status_code=403, detail="Invalid token or expired token. Try login again.")
        return payload

    @staticmethod
    def verify_jwt(jwtoken: str) -> dict:
        try:
            payload = decode_jwt(jwtoken)
        except:
            payload = {}
        return payload


def allow(permissions: Iterable[InstrumentedAttribute], super_permissions: Iterable[InstrumentedAttribute] = None, allow_self=True):
    """
    :param permissions: [BackendPermissionByRole.read_my_org_user, ...]
    :param super_permissions:
    :param allow_self:
    :return:
    """
    if super_permissions is None:
        super_permissions = {BackendPermissionByRole.super_write}
    def decorator_auth(func):
        @wraps(func)
        async def wrapper_auth(*args, **kwargs):
            auth: Dict[str, str] = kwargs['auth']
            same_org: bool = User.org.name in kwargs and kwargs[User.org.name] == auth[User.org.name]
            if allow_self and User.name.name in kwargs and kwargs[User.name.name] == auth[User.name.name] and same_org:
                # self permission
                return await func(*args, **kwargs)
            async with db.create_session_readonly() as s:
                role = select(User.role).filter(User.org == auth['org']).filter(User.name == auth['name']).scalar_subquery()
                result = (await s.execute(select(*permissions, *super_permissions).filter(BackendPermissionByRole.role == role))).one()
            if (any(result[-len(super_permissions):])  # super permisssion
                    or (same_org and any(result[:-len(super_permissions)]))):  # org permission
                return await func(*args, **kwargs)
            raise HTTPException(401, f"Unauthorized. Try to login again.")
        return wrapper_auth
    return decorator_auth
