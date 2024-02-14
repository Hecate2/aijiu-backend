import os
from env import PROD_MARKER
if __name__ == '__main__':
    os.environ[PROD_MARKER] = 'TRUE'
else:
    if os.environ.get(PROD_MARKER, None):
        os.environ.pop(PROD_MARKER)

import uvicorn
from fastapi import FastAPI
import models

app = FastAPI()
import api, mqtt
app.include_router(api.router)
app.include_router(api.org.router)
mqtt.mqtt_data_subscribe.init_app(app)

@app.get("/")
async def app_root():
    return {"Root": "艾灸后端API"}

PORT = 8000

if __name__ == "__main__":
    # asyncio.run(init_tables())
    models.db = models.prod_db
    uvicorn.run(app, host="0.0.0.0", port=PORT)
