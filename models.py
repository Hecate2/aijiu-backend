from asyncio import current_task
from contextlib import asynccontextmanager
import datetime
import os
from typing import Callable
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker, async_scoped_session
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# set the args in system environment for real production
PRODUCTION_USER = os.environ.get('AIJIU_DB_USER', 'postgres')
PRODUCTION_PASSWORD = os.environ.get('AIJIU_DB_PASS', 'a')
PRODUCTION_DATABASE = f"postgresql+asyncpg://{PRODUCTION_USER}:{PRODUCTION_PASSWORD}@localhost:5432/aijiu"
TEST_DATABASE = "postgresql+asyncpg://postgres:a@localhost:5432/aijiu_test"

def datetime_to_string(dt: datetime.datetime) -> str:
    return dt.strftime('%Y/%m/%d, %H:%M:%S')

def datetime_utc_8():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)


class Org(Base):
    __tablename__ = 'org'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    datetime = Column(DateTime, default=datetime_utc_8)
    
    def __str__(self):
        return f"{self.name} created at {self.datetime}"


class ClientId(Base):
    '''
    used as aijiu machine id
    '''
    __tablename__ = 'clientid'
    client_id = Column(String(64), primary_key=True)
    org = Column(String, ForeignKey(f"{Org.__tablename__}.{Org.name.name}", onupdate='CASCADE', ondelete='NO ACTION'), nullable=True)
    org2client = relationship(Org.__name__, backref='client2org')
    datetime = Column(DateTime, default=datetime_utc_8)
    
    def __str__(self):
        return f"{self.client_id}@[{self.org}] {self.datetime}"


class AitiaoPasswd(Base):
    __tablename__ = 'aitiaopasswd'
    passwd = Column(String, primary_key=True)
    client_id = Column(ForeignKey(f"{ClientId.__tablename__}.{ClientId.client_id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)


# class AijiuUser(Base):
#     __tablename__ = 'aijiuuser'
#     username = Column(String(64), primary_key=True)
#     passwd = Column(String(64), nullable=True)
#     org = Column(String, ForeignKey(f"{Org.__tablename__}.{Org.name.name}", onupdate='CASCADE', ondelete='NO ACTION'), nullable=True)
#     org2user = relationship(Org.__name__, backref='user2org')
#     datetime = Column(DateTime, default=datetime_utc_8)
#
#     def __str__(self):
#         return f"{self.username}@[{self.org}] {self.datetime}"

class User(Base):
    __tablename__ = 'backenduser'
    name = Column(String(64), primary_key=True)
    passwd = Column(String(64), nullable=True)  # sha256 result
    org = Column(String, ForeignKey(f"{Org.__tablename__}.{Org.name.name}", onupdate='CASCADE', ondelete='NO ACTION'), nullable=True)
    org2user = relationship(Org.__name__, backref='user2org')
    datetime = Column(DateTime, default=datetime_utc_8)

    def __str__(self):
        return f"{self.name}@[{self.org}] {self.datetime}"

class AitiaoLife(Base):
    __tablename__ = 'aitiaolife'
    client_id = Column(ForeignKey(f"{ClientId.__tablename__}.{ClientId.client_id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2life = relationship(ClientId.__name__, backref='life2client')
    # user2life = relationship(AijiuUser.__name__, backref='life2user')
    aitiao_life = Column(Integer)  # in seconds
    
    def __str__(self):
        m, s = divmod(self.aitiao_life, 60)
        h, m = divmod(m, 60)
        return f"{self.username} remaining life {'%d:%02d:%02d' % (h, m, s)} at {self.timestamp}"


class AijiuStartEnd(Base):
    __tablename__ = 'aijiustartend'
    client_id = Column(ForeignKey(f"{ClientId.__tablename__}.{ClientId.client_id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2startend = relationship(ClientId.__name__, backref='startend2client')
    # user2startend = relationship(AijiuUser.__name__, backref='startend2user')
    start_end = Column(Boolean)
    
    def __str__(self):
        return f"{self.username} {'starts' if self.start_end else 'ends'} at {self.timestamp}"


class AijiuRemainingTime(Base):
    __tablename__ = 'aijiuremainingtime'
    client_id = Column(ForeignKey(f"{ClientId.__tablename__}.{ClientId.client_id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2remainingtime = relationship(ClientId.__name__, backref='remainingtime2client')
    # user2startend = relationship(AijiuUser.__name__, backref='startend2user')
    remaining_time = Column(Integer)
    
    def __str__(self):
        return f"{self.username} {'starts' if self.start_end else 'ends'} at {self.timestamp}"


class AijiuTemperature(Base):
    __tablename__ = 'aijiutemperature'
    client_id = Column(ForeignKey(f"{ClientId.__tablename__}.{ClientId.client_id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    device_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2temp = relationship(ClientId.__name__, backref='temp2client')
    # user2temp = relationship(AijiuUser.__name__, backref='temp2user')
    temperature = Column(Integer)
    
    def __str__(self):
        return f"{self.username} catalyst {self.temperature}℃ at {self.timestamp}"


class CatalystTemperature(Base):
    __tablename__ = 'catalysttemperature'
    client_id = Column(ForeignKey(f"{ClientId.__tablename__}.{ClientId.client_id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    device_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2catalyst = relationship(ClientId.__name__, backref='catalyst2client')
    # user2catalyst = relationship(AijiuUser.__name__, backref='catalyst2user')
    temperature = Column(Integer)
    
    def __str__(self):
        return f"{self.username} catalyst {self.temperature}℃ at {self.timestamp}"


class FanRpm(Base):
    __tablename__ = 'fanrpm'
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey(f"{ClientId.__tablename__}.{ClientId.client_id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    device_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2fan = relationship(ClientId.__name__, backref='fan2client')
    # user2fan = relationship(AijiuUser.__name__, backref='fan2user')
    rpm = Column(Integer)
    
    def __str__(self):
        return f"{self.client_id} {self.username} fan {self.rpm}rpm at {self.timestamp}"


time_series_tables = {AitiaoLife, AijiuStartEnd, AijiuTemperature, CatalystTemperature, FanRpm}

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

async def init_tables(engine = test_engine, name = ROOT):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    # create root org and root user
    async with db.create_session() as s:
        async with s.begin():
            if (await s.execute(select(Org).filter(Org.name == name))).one_or_none() is None:
                s.add(Org(name=name))
            if (await s.execute(select(User).filter(User.name == name))).one_or_none() is None:
                s.add(User(name=name, passwd=name, org=name))


async def drop_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)