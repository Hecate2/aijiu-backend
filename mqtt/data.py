from typing import Any
from env import MQTT_CLIENT_ID, MQTT_CONFIG
import json
from gmqtt import Client as MQTTClient
from fastapi_mqtt import FastMQTT
from database.models import AijiuStartEnd, AijiuRemainingTime, AijiuTemperature, CatalystTemperature, FanRpm, GPSPosition
from database.connection import db
from mqtt.auth import naive验证艾条密码, 艾条密码被同一组织使用过
mqtt_data_subscribe = FastMQTT(config=MQTT_CONFIG, client_id=MQTT_CLIENT_ID)

@mqtt_data_subscribe.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    print("Connected: ", client.protocol_version, flags, rc, properties)

@mqtt_data_subscribe.subscribe("艾条密码/+")
async def 艾条密码(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    client_id = topic.split('/')[1]
    密码 = json.loads(payload.decode())['密码']
    print(topic, client_id, json.loads(payload.decode()))
    if naive验证艾条密码(密码):
        async for result in 艾条密码被同一组织使用过(client_id, 密码):
            if result:
                mqtt_data_subscribe.publish(f'艾条有效秒数增加/{client_id}', payload={"增加秒数": 200}, qos=2)

@mqtt_data_subscribe.subscribe("灸疗开始/+")
async def 灸疗开始(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    client_id = topic.split('/')[1]
    payload = json.loads(payload.decode())
    定时, timestamp = payload['定时'], payload['ts']
    async with db.create_session() as s:
        s.add(AijiuStartEnd(client_id=client_id, timestamp=timestamp, start_end=True))
        s.add(AijiuRemainingTime(client_id=client_id, timestamp=timestamp, remaining_time=定时))

@mqtt_data_subscribe.subscribe("灸疗结束/+")
async def 灸疗结束(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    client_id = topic.split('/')[1]
    payload = json.loads(payload.decode())
    timestamp = payload['ts']
    async with db.create_session() as s:
        s.add(AijiuStartEnd(client_id=client_id, timestamp=timestamp, start_end=False))
        s.add(AijiuRemainingTime(client_id=client_id, timestamp=timestamp, remaining_time=0))

@mqtt_data_subscribe.subscribe("灸疗剩余时间/+")
async def 灸疗剩余时间(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    client_id = topic.split('/')[1]
    payload = json.loads(payload.decode())
    剩余时间, timestamp = payload['剩余时间'], payload['ts']
    async with db.create_session() as s:
        s.add(AijiuRemainingTime(client_id=client_id, timestamp=timestamp, remaining_time=剩余时间))

@mqtt_data_subscribe.subscribe("灸疗温度/+/+")
async def 灸疗温度(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    _, client_id, device_id = topic.split('/')
    payload = json.loads(payload.decode())
    温度, timestamp = payload['温度'], payload['ts']
    async with db.create_session() as s:
        s.add(AijiuTemperature(client_id=client_id, device_id=int(device_id), timestamp=timestamp, temperature=温度))

@mqtt_data_subscribe.subscribe("三元催化温度/+/+")
async def 三元催化温度(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    _, client_id, device_id = topic.split('/')
    payload = json.loads(payload.decode())
    温度, timestamp = payload['温度'], payload['ts']
    async with db.create_session() as s:
        s.add(CatalystTemperature(client_id=client_id, device_id=int(device_id), timestamp=timestamp, temperature=温度))

@mqtt_data_subscribe.subscribe("散热风机转速/+/+")
async def 散热风机转速(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    _, client_id, device_id = topic.split('/')
    payload = json.loads(payload.decode())
    转速, timestamp = payload['转速'], payload['ts']
    async with db.create_session() as s:
        s.add(FanRpm(client_id=client_id, device_id=int(device_id), timestamp=timestamp, rpm=转速))

@mqtt_data_subscribe.subscribe("GPS定位/+")
async def GPS定位(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    _, client_id = topic.split('/')
    payload = json.loads(payload.decode())
    timestamp = payload['ts']
    async with db.create_session() as s:
        s.add(GPSPosition(client_id=client_id, timestamp=timestamp, degreeE=payload['E'], degreeN=payload['N']))
