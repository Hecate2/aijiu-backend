import os
from hashlib import sha512
from passlib.context import CryptContext
from typing import Union
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body
from api.version import API_PREFIX
from database.models import User, BackendPermissionByRole
from sqlalchemy import select, func, update, delete
from database.connection import db
from utils import jsonify

SECRET_KEY = "艾灸后端foobar阿巴阿巴"
SECRET_KEY_PATH = './cryptography/aijiu_secret_key.txt'
if os.path.isfile(SECRET_KEY_PATH):
    with open(SECRET_KEY_PATH, 'r') as f:
        SECRET_KEY = sha512(f.read().strip().encode('utf-8')).hexdigest()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
REFRESH_TOKEN_EXPIRE_MINUTES = 120


def create_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db, username: str):
  if username in db:
    user = db[username]
    return User(**user)

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
async def login(username: str = Body(), passwd = Body()):
    print(f"username: {username}")
    print(f"passwd length: {len(passwd)}")
    return {"success": True}

# TODO: change user role
# TODO: change passwd

@router.get('/permission/{org}/{username}')
async def get_permission(org: str, username: str):
    async with db.create_session_readonly() as s:
        async with s.begin():
            role = (await s.execute(select(User.role).filter(User.org == org).filter(User.name == username))).one()[0]
            permission = (await s.execute(select(*BackendPermissionByRole.__table__.columns).filter_by(role=role))).one()
            return jsonify(permission)