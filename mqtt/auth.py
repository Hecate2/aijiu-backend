from fastapi import APIRouter
from api.version import API_PREFIX
mqtt_auth_router = APIRouter(
    prefix= API_PREFIX + '/mqttauth',
    tags = ['mqttauth']
)

@mqtt_auth_router.post('/')
async def mqtt_auth(clientid: str = '', peerhost: str = ''):
    # TODO
    return {"result": "allow"}