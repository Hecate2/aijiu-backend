import os
import ssl
import httpx
from fastapi_mqtt import MQTTConfig

cert = ssl.SSLContext()
# cert.load_cert_chain('../u385ba0f.ala.asia-southeast1.emqxsl.com.emqxsl-ca.crt')

MQTT_CONFIG = MQTTConfig(
    # host="localhost",
    # port=1883,
    host="u385ba0f.ala.asia-southeast1.emqxsl.com",
    port=8883,
    keepalive=5,
    username="aijiu-backend",
    password="aijiu",
    ssl=cert
)
MQTT_CLIENT_ID = 'aijiu-backend'
PROD_MARKER = 'AIJIU_PROD'
ROOT = 'root'
ORG_ADMIN = 'org_admin'
ORG_USER = 'org_user'

# EMQX_USERNAME = "955b89e5df8bcf4c"
# EMQX_PASSWD = "LlujOHHu1NONPjb5Ta5r9BJCX8dxL8cad9CaRwKYIz4QI"
EMQX_USERNAME = "u53c45b2"
EMQX_PASSWD = "r1b51425773f361e"
# EMQX_API_PORT = 18083
EMQX_API_PORT = 8443
EMQX_HTTP_CLIENT = httpx.AsyncClient(
    base_url=f'https://{MQTT_CONFIG.host}:{EMQX_API_PORT}/api/v5',
    auth=httpx.BasicAuth(username=EMQX_USERNAME, password=EMQX_PASSWD)
    # headers={'Authorization':'Basic OTU1Yjg5ZTVkZjhiY2Y0YzpMbHVqT0hIdTFOT05QamI1VGE1cjlCSkNYOGR4TDhjYWQ5Q2FSd0tZSXo0UUk='}
)

def is_prod_env() -> bool: return os.environ.get(PROD_MARKER, 'FALSE') == 'TRUE'
def set_prod_env(): os.environ[PROD_MARKER] = 'TRUE'
def ensure_non_prod_env():
    if os.environ.get(PROD_MARKER, None):
        os.environ.pop(PROD_MARKER)