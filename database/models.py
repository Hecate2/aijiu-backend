import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

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


class AijiuMachine(Base):
    '''
    aijiu machines id
    '''
    __tablename__ = 'aijiumachine'
    id = Column(String(64), primary_key=True)
    org = Column(String, ForeignKey(f"{Org.__tablename__}.{Org.name.name}", onupdate='CASCADE', ondelete='NO ACTION'), nullable=False)
    org2client = relationship(Org.__name__, backref='client2org')
    datetime = Column(DateTime, default=datetime_utc_8)
    
    def __str__(self):
        return f"{self.id}@[{self.org}] {self.datetime}"


class AitiaoPasswd(Base):
    __tablename__ = 'aitiaopasswd'
    passwd = Column(String, primary_key=True)
    client_id = Column(ForeignKey(f"{AijiuMachine.__tablename__}.{AijiuMachine.id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
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

class BackendPermissionByRole(Base):
    __tablename__ = 'backendpermissionbyrole'
    role = Column(String(16), primary_key=True)
    super_read = Column(Boolean)
    super_write = Column(Boolean)
    write_my_org_user = Column(Boolean)
    read_my_org_user = Column(Boolean)
    write_my_org_aijiu_client = Column(Boolean)
    read_my_org_aijiu_client = Column(Boolean)
    
# TODO: init basic roles when app launched
basic_roles = {
    BackendPermissionByRole(role='...')
}

class User(Base):
    __tablename__ = 'backenduser'
    name = Column(String(64), primary_key=True)
    passwd = Column(String(64), nullable=True)  # sha256 result
    org = Column(String, ForeignKey(f"{Org.__tablename__}.{Org.name.name}", onupdate='CASCADE', ondelete='NO ACTION'), nullable=True)
    org2user = relationship(Org.__name__, backref='user2org')
    role = Column(String(16), ForeignKey(f"{BackendPermissionByRole.__tablename__}.{BackendPermissionByRole.role.name}",
                                    onupdate='CASCADE', ondelete='RESTRICT'))
    datetime = Column(DateTime, default=datetime_utc_8)

    def __str__(self):
        return f"{self.name}@[{self.org}] {self.datetime}"

class AitiaoLife(Base):
    __tablename__ = 'aitiaolife'
    client_id = Column(ForeignKey(f"{AijiuMachine.__tablename__}.{AijiuMachine.id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2life = relationship(AijiuMachine.__name__, backref='life2client')
    # user2life = relationship(AijiuUser.__name__, backref='life2user')
    aitiao_life = Column(Integer)  # in seconds
    
    def __str__(self):
        m, s = divmod(self.aitiao_life, 60)
        h, m = divmod(m, 60)
        return f"{self.username} remaining life {'%d:%02d:%02d' % (h, m, s)} at {self.timestamp}"


class AijiuStartEnd(Base):
    __tablename__ = 'aijiustartend'
    client_id = Column(ForeignKey(f"{AijiuMachine.__tablename__}.{AijiuMachine.id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2startend = relationship(AijiuMachine.__name__, backref='startend2client')
    # user2startend = relationship(AijiuUser.__name__, backref='startend2user')
    start_end = Column(Boolean)
    
    def __str__(self):
        return f"{self.username} {'starts' if self.start_end else 'ends'} at {self.timestamp}"


class AijiuRemainingTime(Base):
    __tablename__ = 'aijiuremainingtime'
    client_id = Column(ForeignKey(f"{AijiuMachine.__tablename__}.{AijiuMachine.id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2remainingtime = relationship(AijiuMachine.__name__, backref='remainingtime2client')
    # user2startend = relationship(AijiuUser.__name__, backref='startend2user')
    remaining_time = Column(Integer)
    
    def __str__(self):
        return f"{self.username} {'starts' if self.start_end else 'ends'} at {self.timestamp}"


class AijiuTemperature(Base):
    __tablename__ = 'aijiutemperature'
    client_id = Column(ForeignKey(f"{AijiuMachine.__tablename__}.{AijiuMachine.id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    device_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2temp = relationship(AijiuMachine.__name__, backref='temp2client')
    # user2temp = relationship(AijiuUser.__name__, backref='temp2user')
    temperature = Column(Integer)
    
    def __str__(self):
        return f"{self.username} catalyst {self.temperature}℃ at {self.timestamp}"


class CatalystTemperature(Base):
    __tablename__ = 'catalysttemperature'
    client_id = Column(ForeignKey(f"{AijiuMachine.__tablename__}.{AijiuMachine.id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    device_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2catalyst = relationship(AijiuMachine.__name__, backref='catalyst2client')
    # user2catalyst = relationship(AijiuUser.__name__, backref='catalyst2user')
    temperature = Column(Integer)
    
    def __str__(self):
        return f"{self.username} catalyst {self.temperature}℃ at {self.timestamp}"


class FanRpm(Base):
    __tablename__ = 'fanrpm'
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey(f"{AijiuMachine.__tablename__}.{AijiuMachine.id.name}", onupdate='CASCADE', ondelete='NO ACTION'),
                       primary_key=True)
    device_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime_utc_8, primary_key=True)
    # username = Column(ForeignKey(f"{AijiuUser.__tablename__}.{AijiuUser.username.name}", onupdate='CASCADE', ondelete='NO ACTION'))
    client2fan = relationship(AijiuMachine.__name__, backref='fan2client')
    # user2fan = relationship(AijiuUser.__name__, backref='fan2user')
    rpm = Column(Integer)
    
    def __str__(self):
        return f"{self.client_id} {self.username} fan {self.rpm}rpm at {self.timestamp}"


time_series_tables = {AitiaoLife, AijiuStartEnd, AijiuTemperature, CatalystTemperature, FanRpm}
