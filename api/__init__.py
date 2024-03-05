import api.org, api.user
from api.version import API_PREFIX
from fastapi import APIRouter
router = APIRouter(
    prefix= API_PREFIX,
    tags = ['root']
)
@router.get('/')
async def root():
    return {"api/v1": "艾灸后端API/v1"}
