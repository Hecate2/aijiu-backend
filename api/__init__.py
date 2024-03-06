import api.org, api.user, api.aijiu_machine, api.auth
from api.version import API_PREFIX
from fastapi import APIRouter
router = APIRouter(
    prefix= API_PREFIX,
    tags = ['root']
)
@router.get('/')
async def root():
    return {"api/v1": "艾灸后端API/v1"}
