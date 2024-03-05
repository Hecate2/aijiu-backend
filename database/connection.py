import os
from typing import Callable
import asyncpg
from asyncio import current_task
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, async_scoped_session, create_async_engine
from database.models import Org, User, Base
# set the args in system environment for real production
PRODUCTION_USER = os.environ.get('AIJIU_DB_USER', 'postgres')
PRODUCTION_PASSWORD = os.environ.get('AIJIU_DB_PASS', 'a')
PRODUCTION_DATABASE = f"postgresql+asyncpg://{PRODUCTION_USER}:{PRODUCTION_PASSWORD}@localhost:5432/aijiu"
TEST_DATABASE = "postgresql+asyncpg://postgres:a@localhost:5432/aijiu_test"

POOL_SIZE = 20
POOL_RECYCLE = 3600
POOL_TIMEOUT = 15
MAX_OVERFLOW = 2
CONNECT_TIMEOUT = 60

def get_async_engine(url: str = TEST_DATABASE, echo=False):
    return create_async_engine(
        url=url,
        echo=echo,
        pool_size=POOL_SIZE,
        pool_recycle=POOL_RECYCLE,
        pool_timeout=POOL_TIMEOUT,
        max_overflow=MAX_OVERFLOW,
        connect_args={"timeout": CONNECT_TIMEOUT}
    )
test_engine = get_async_engine(TEST_DATABASE)
prod_engine = get_async_engine(PRODUCTION_DATABASE)

async def connect_create_if_not_exists(user, passwd, database):
    try:
        conn = await asyncpg.connect(user=user, password=passwd, database=database)
    except Exception:
        # Database does not exist, create it.
        sys_conn = await asyncpg.connect(user=user, password=passwd)
        await sys_conn.execute(f'CREATE DATABASE "{database}" OWNER "{user}"')
        await sys_conn.close()
        # Connect to the newly created database.
        conn = await asyncpg.connect(user=user, password=passwd, database=database)
    return conn


class DatabaseManager:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.async_session_maker = async_sessionmaker(self.engine, class_=AsyncSession)
    
    def cleanup(self):
        if self.engine:
            self.engine.dispose()
    
    @asynccontextmanager
    async def create_session(self, auto_commit=True, scope_func: Callable = current_task) -> AsyncSession:
        session = async_scoped_session(self.async_session_maker, scopefunc=scope_func)
        try:
            yield session
            if auto_commit:
                await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
    
    @asynccontextmanager
    async def create_session_readonly(self, scope_func: Callable = current_task) -> AsyncSession:
        session = async_scoped_session(self.async_session_maker, scopefunc=scope_func)
        try:
            yield session
        except Exception as e:
            raise e
        finally:
            await session.close()


test_db = DatabaseManager(test_engine)
prod_db = DatabaseManager(prod_engine)

from env import PROD_MARKER

if os.environ.get(PROD_MARKER, None) == 'TRUE':
    db = prod_db
else:
    db = test_db

ROOT = 'root'


async def init_tables(engine=test_engine, org_name=ROOT):
    await connect_create_if_not_exists(user=test_engine.url.username, passwd=test_engine.url.password, database=test_engine.url.database)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    # create root org and root user
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(Org).filter(Org.name == org_name))).one_or_none() is None:
                s.add(Org(name=org_name))
            if (await s.execute(select(User).filter(User.name == org_name))).one_or_none() is None:
                s.add(User(name=org_name, passwd=org_name, org=org_name))


async def drop_tables():
    await connect_create_if_not_exists(user=test_engine.url.username, passwd=test_engine.url.password, database=test_engine.url.database)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)