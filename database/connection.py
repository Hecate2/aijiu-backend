import os
from typing import Callable, Union
import asyncpg
from asyncio import current_task
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, async_scoped_session, create_async_engine
from database.models import Org, ParentOrg, User, BackendPermissionByRole, BASIC_ROLES, Base
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

async def create_database_if_not_exists(user, passwd, database):
    try:
        conn = await asyncpg.connect(user=user, password=passwd, database=database)
    except Exception:
        # Database does not exist, create it.
        sys_conn = await asyncpg.connect(user=user, password=passwd)
        sql = f'CREATE DATABASE "{database}" OWNER "{user}"'
        # print(sql)
        await sys_conn.execute(sql)
        await sys_conn.close()
        # Connect to the newly created database.
        conn = await asyncpg.connect(user=user, password=passwd, database=database)
    return conn


async def drop_database_inner(user, passwd, database):
    try:
        conn = await asyncpg.connect(user=user, password=passwd, database=database)
        await conn.execute(f'DROP DATABASE "{database}"')
        await conn.close()
    except Exception:
        pass


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

from env import PROD_MARKER, ROOT

if os.environ.get(PROD_MARKER, None) == 'TRUE':
    db = prod_db
else:
    db = test_db


async def init_tables(engine=test_engine, initial_org_name=ROOT):
    await create_database_if_not_exists(user=engine.url.username, passwd=engine.url.password, database=engine.url.database)
    async with engine.begin() as conn:
        # print(f"Initializing tables with {engine.url}")
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    db = DatabaseManager(engine)
    # create root org and root user
    async with db.create_session() as s:
        async with s.begin():
            if not (await s.execute(select(BackendPermissionByRole))).first():
                # print(f"Inserting basic roles")
                for role in BASIC_ROLES:
                    s.add(role)
            if (await s.execute(select(Org).filter(Org.name == initial_org_name))).one_or_none() is None:
                # print(f"Inserting root org {initial_org_name}")
                s.add(Org(name=initial_org_name, authLevel=0))
                if os.environ.get(PROD_MARKER, None) == 'TRUE':
                    for i in range(3):
                        test_org_name = f'测试组织{i}，可以无视或删除'
                        s.add(Org(name=test_org_name, authLevel=1))
                        s.add(ParentOrg(org=test_org_name, parentOrg = initial_org_name))
            if (await s.execute(select(User).filter(User.name == initial_org_name))).one_or_none() is None:
                # print(f"Inserting root user {initial_org_name}")
                s.add(User(name=initial_org_name, passwd=initial_org_name, org=initial_org_name, role=ROOT))


async def drop_tables(engine=test_engine):
    await create_database_if_not_exists(user=engine.url.username, passwd=engine.url.password, database=engine.url.database)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def drop_database(engine=test_engine):
    await drop_database_inner(engine.url.username, engine.url.password, engine.url.database)
