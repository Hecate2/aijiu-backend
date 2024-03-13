import os
from hashlib import sha512
from typing import Union
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body, HTTPException
from api.version import API_PREFIX
from database.models import User, BackendPermissionByRole
from sqlalchemy import select, func, update, delete
from database.connection import db
from utils import jsonify, datetime_utc_8
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

class PermissionChecker:
    # TODO: baked queries
    @staticmethod
    async def can_write_org(org: str, user: str) -> bool:
        return True
    @staticmethod
    async def can_read_org(org: str, user: str) -> bool:
        return True
    @staticmethod
    async def can_write_all_orgs(user: str) -> bool:
        return True
    @staticmethod
    async def can_read_all_orgs(user: str) -> bool:
        return True
    def __call__(self, user: User):
        return True
    
router = APIRouter(
    prefix= API_PREFIX + '/auth',
    tags = ['auth']
)

@router.post('/login/')
async def login(org: str = Body(), user: str = Body(), passwd = Body()):
    async with db.create_session_readonly() as s:
        try:
            user = (await s.execute(select(User.org, User.name, User.role, User.passwd).filter(User.org == org).filter(User.name == user))).one_or_none()
        except Exception:
            raise HTTPException(400, f"{User.__name__} {user} in {org} does not exist")
    if user.passwd == None or user.passwd == passwd or user.passwd == sha512((passwd + SECRET_KEY).encode('utf-8')).digest():
        return {"token": encode_jwt({
            User.org.name: user.org,
            User.name.name: user.name,
            User.role.name: user.role,
        })}
    raise HTTPException(400, f"Incorrect passwd for user {user} in {org}")

# TODO: change user role
# TODO: change passwd

@router.get('/permission/{org}/{username}')
async def get_permission(org: str, username: str):
    async with db.create_session_readonly() as s:
        async with s.begin():
            role = (await s.execute(select(User.role).filter(User.org == org).filter(User.name == username))).one()[0]
            permission = (await s.execute(select(*BackendPermissionByRole.__table__.columns).filter_by(role=role))).one()
            return jsonify(permission)