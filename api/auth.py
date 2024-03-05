import os
from hashlib import sha512
from database.models import User
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "艾灸后端foobar阿巴阿巴"
SECRET_KEY_PATH = './cryptography/aijiu_secret_key.txt'
if os.path.isfile(SECRET_KEY_PATH):
    with open(SECRET_KEY_PATH, 'r') as f:
        SECRET_KEY = sha512(f.read().strip().encode('utf-8')).hexdigest()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
REFRESH_TOKEN_EXPIRE_MINUTES = 120


def create_token(data: dict, expires_delta: timedelta | None = None):
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