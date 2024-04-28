import datetime
from typing import Any
from env import MQTT_CLIENT_ID, MQTT_CONFIG
import json
from gmqtt import Client as MQTTClient
from fastapi_mqtt import FastMQTT
from database.models import AitiaoLife, AijiuStartEnd, AijiuRemainingTime, AijiuTemperature, CatalystTemperature, FanRpm, GPSPosition
from database.connection import db
from mqtt.auth import naive验证艾条密码, 艾条密码被同一组织使用过
mqtt_data_subscribe = FastMQTT(config=MQTT_CONFIG, client_id=MQTT_CLIENT_ID)

@mqtt_data_subscribe.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    print("Connected: ", client.protocol_version, flags, rc, properties)

@mqtt_data_subscribe.subscribe("艾条密码")
async def 艾条密码(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    payload = json.loads(payload.decode())
    密码, client_id = payload['密码'], str(payload['client_id'])
    print(topic, payload)
    if naive验证艾条密码(密码):
        async for result in 艾条密码被同一组织使用过(client_id, 密码):
            if result:
                mqtt_data_subscribe.publish(f'艾条有效秒数增加/{client_id}', payload={"增加秒数": 200}, qos=2)

@mqtt_data_subscribe.subscribe("艾条有效秒数")
async def 艾条有效秒数(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    payload = json.loads(payload.decode())
    有效秒数, client_id = payload['有效秒数'], payload['client_id']
    print(topic, client_id, json.loads(payload.decode()))
    async with db.create_session() as s:
        s.add(AitiaoLife(client_id=client_id, aitiao_life=有效秒数))

@mqtt_data_subscribe.subscribe("灸疗启停/+")
async def 灸疗启停(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    device_id = int(topic.split('/')[1])
    payload = json.loads(payload.decode())
    print(topic, payload)
    定时, 模式, 启停, client_id, timestamp = payload['定时'], payload['模式'], int(payload['启停']), str(payload['client_id']), datetime.datetime.fromisoformat(payload['ts'])
    async with db.create_session() as s:
        s.add(AijiuStartEnd(client_id=client_id, device_id=device_id, timestamp=timestamp, start_end=True if 启停 else False))
        s.add(AijiuRemainingTime(client_id=client_id, device_id=int(device_id), timestamp=timestamp, remaining_time=定时))

@mqtt_data_subscribe.subscribe("灸疗剩余时间/+")
async def 灸疗剩余时间(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    device_id = int(topic.split('/')[1])
    payload = json.loads(payload.decode())
    剩余时间, client_id, timestamp = payload['剩余时间'], str(payload['client_id']), datetime.datetime.fromisoformat(payload['ts'])
    async with db.create_session() as s:
        s.add(AijiuRemainingTime(client_id=client_id, device_id=int(device_id), timestamp=timestamp, remaining_time=剩余时间))

@mqtt_data_subscribe.subscribe("灸疗温度/+")
async def 灸疗温度(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    device_id = int(topic.split('/')[1])
    payload = json.loads(payload.decode())
    温度, client_id, timestamp = payload['温度'], str(payload['client_id']), datetime.datetime.fromisoformat(payload['ts'])
    async with db.create_session() as s:
        s.add(AijiuTemperature(client_id=client_id, device_id=int(device_id), timestamp=timestamp, temperature=温度))

@mqtt_data_subscribe.subscribe("三元催化温度/+")
async def 三元催化温度(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    device_id = int(topic.split('/')[1])
    payload = json.loads(payload.decode())
    温度, client_id, timestamp = payload['温度'], str(payload['client_id']), datetime.datetime.fromisoformat(payload['ts'])
    async with db.create_session() as s:
        s.add(CatalystTemperature(client_id=client_id, device_id=int(device_id), timestamp=timestamp, temperature=温度))

@mqtt_data_subscribe.subscribe("散热风机转速/+")
async def 散热风机转速(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    device_id = int(topic.split('/')[1])
    payload = json.loads(payload.decode())
    转速, client_id, timestamp = payload['转速'], str(payload['client_id']), datetime.datetime.fromisoformat(payload['ts'])
    async with db.create_session() as s:
        s.add(FanRpm(client_id=client_id, device_id=int(device_id), timestamp=timestamp, rpm=转速))

@mqtt_data_subscribe.subscribe("GPS定位")
async def GPS定位(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    payload = json.loads(payload.decode())
    client_id, timestamp = str(payload['client_id']), datetime.datetime.fromisoformat(payload['ts'])
    async with db.create_session() as s:
        s.add(GPSPosition(client_id=client_id, timestamp=timestamp, degreeE=payload['E'], degreeN=payload['N']))
