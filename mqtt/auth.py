from typing import AsyncIterable
from fastapi import APIRouter
from api.version import API_PREFIX
from database.models import AitiaoPasswd, AijiuMachine
from database.connection import db
from sqlalchemy import select

mqtt_auth_router = APIRouter(
    prefix= API_PREFIX + '/mqttauth',
    tags = ['mqttauth']
)

@mqtt_auth_router.post('/')
async def mqtt_auth(clientid: str = '', peerhost: str = ''):
    # TODO
    return {"result": "allow_read"}

def naive验证艾条密码(passwd: str) -> bool:
    """
    This func is for testing and not for production...
    :param passwd: 5-digit y, 2-digit x, 1 digit b
    :return: y == x**2 + x*b
    """
    if len(passwd) != 8: return False
    if not passwd.isdigit(): return False
    y, x, b = int(passwd[:5]), int(passwd[5:7]), int(passwd[7:8])
    return y == x*(x+b)

async def 艾条密码被同一组织使用过(client_id: str, passwd: str) -> AsyncIterable[bool]:
    async with db.create_session(auto_commit=False) as s:
        async with s.begin():
            all_same_passwd_clients = select(AitiaoPasswd.client_id).filter(AitiaoPasswd.passwd == passwd)
            all_same_passwd_orgs = await s.execute(select(AijiuMachine.org).filter(AijiuMachine.id.in_(all_same_passwd_clients)).distinct())
            this_client_org = await s.execute(select(AijiuMachine.org).filter(AijiuMachine.id == client_id))
            if this_client_org in all_same_passwd_orgs:
                yield False
            s.add(AitiaoPasswd(passwd=passwd, client_id=client_id))
        yield True
        # 如果yield后服务器死机了，我还没commit，那就是我服务器的锅，艾条时间免费送你了
        # TODO: 分布式重型日志/消息队列，确保死机重启后也能增加艾条寿命
        await s.commit()