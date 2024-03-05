# This service subscribes messages from MQTT broker
# and sends them to the time scale database

# from datetime import datetime, timedelta
from paho.mqtt import client as mqtt_client


broker = 'localhost'
port = 1883
subscribe_topic = "艾条密码/+"
# generate client ID with pub prefix randomly
client_id = f'aijiu-test'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(client_id, password='a')
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client: mqtt_client.Client, client_id: str):
    # now = datetime.utcnow() + timedelta(hours=8)
    msg = '{"增加秒数": 200}'
    publish_topic = f"艾条有效秒数增加/{client_id}"
    result = client.publish(publish_topic, msg, qos=2)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{publish_topic}`")
    else:
        print(f"Failed to send message to topic {publish_topic}")

def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        client_id = msg.topic.split('/')[-1]
        publish(client, client_id)

    client.subscribe(subscribe_topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()