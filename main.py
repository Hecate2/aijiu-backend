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
from api import router
app.include_router(router)


@app.get("/")
async def app_root():
    return {"Root": "艾灸后端API"}

PORT = 8000

if __name__ == "__main__":
    # asyncio.run(init_tables())
    models.db = models.prod_db
    uvicorn.run(app, host="0.0.0.0", port=PORT)
