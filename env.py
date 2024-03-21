import os
from fastapi_mqtt import MQTTConfig

MQTT_CONFIG = MQTTConfig(
    host="localhost",
    port=1883,
    keepalive=5,
    # username="username",
    # password="strong_password",
)
MQTT_CLIENT_ID = 'aijiu-backend'
PROD_MARKER = 'AIJIU_PROD'
ROOT = 'root'
ORG_ADMIN = 'org_admin'
ORG_USER = 'org_user'

def is_prod_env() -> bool: return os.environ.get(PROD_MARKER, 'FALSE') == 'TRUE'
def set_prod_env(): os.environ[PROD_MARKER] = 'TRUE'
def ensure_non_prod_env():
    if os.environ.get(PROD_MARKER, None):
        os.environ.pop(PROD_MARKER)