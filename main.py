import os
from env import PROD_MARKER
if __name__ == '__main__':
    os.environ[PROD_MARKER] = 'TRUE'
else:
    if os.environ.get(PROD_MARKER, None):
        os.environ.pop(PROD_MARKER)

from fastapi import FastAPI
from database import connection

app = FastAPI()
import api
app.include_router(api.router)
app.include_router(api.org.router)
app.include_router(api.user.router)
app.include_router(api.aijiu_machine.router)
app.include_router(api.auth.router)


@app.get("/")
async def app_root():
    return {"Root": "艾灸后端API"}

PORT = 8000

if __name__ == "__main__":
    # asyncio.run(init_tables())
    connection.db = connection.prod_db
    import asyncio
    import mqtt
    mqtt.mqtt_data_subscribe.init_app(app)
    from uvicorn import Config, Server
    loop = asyncio.get_event_loop()
    config = Config(app=app, loop="asyncio")
    server = Server(config)
    loop.run_until_complete(connection.init_tables(engine=connection.prod_engine))
    loop.run_until_complete(server.serve())
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=PORT)
    # from multiprocessing import Process
    # app_process = Process(name='艾灸后端', target=uvicorn.run, args=(app, ), kwargs={"host": "0.0.0.0", "port": PORT}, daemon=True)
    # app_process.start()

    

