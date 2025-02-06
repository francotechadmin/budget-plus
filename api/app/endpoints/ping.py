from fastapi import APIRouter

router = APIRouter()

@router.get("/ping", summary="Health check endpoint")
async def pong():
    return {"ping": "pong!"}
