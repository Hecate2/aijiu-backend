import os
from env import set_prod_env, ensure_non_prod_env
if __name__ == '__main__':
    set_prod_env()
else:
    ensure_non_prod_env()

from fastapi import FastAPI
from database import connection

app = FastAPI()
import api
app.include_router(api.router)
app.include_router(api.org.router)
app.include_router(api.user.router)
app.include_router(api.aijiu_machine.router)
app.include_router(api.auth.router)

from fastapi.middleware.cors import CORSMiddleware

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.get("/")
# async def app_root():
#     return {"Root": "艾灸后端API"}

PORT = 58000

if __name__ == "__main__":
    FRONTEND_FILES_DIR = "dist"
    from fastapi.staticfiles import StaticFiles
    if not os.path.isdir(FRONTEND_FILES_DIR):
        os.makedirs(FRONTEND_FILES_DIR)
    if not os.listdir(FRONTEND_FILES_DIR):
        print("没有前端文件。必须运行单独的前端服务器")
    app.mount("/", StaticFiles(directory=FRONTEND_FILES_DIR, html = True), name="static")
    # asyncio.run(init_tables())
    connection.db = connection.prod_db
    import asyncio
    import mqtt
    mqtt.mqtt_data_subscribe.init_app(app)
    from uvicorn import Config, Server
    loop = asyncio.get_event_loop()
    config = Config(app=app, loop="asyncio", port=PORT)
    server = Server(config)
    loop.run_until_complete(connection.init_tables(engine=connection.prod_engine))
    loop.run_until_complete(server.serve())
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=PORT)
    # from multiprocessing import Process
    # app_process = Process(name='艾灸后端', target=uvicorn.run, args=(app, ), kwargs={"host": "0.0.0.0", "port": PORT}, daemon=True)
    # app_process.start()

    

