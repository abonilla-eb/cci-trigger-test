from fastapi import APIRouter
from fastapi.responses import JSONResponse

from server.models import Challenge
from server.connection_manager import manager
from server.utilities_server_event import make_challenge

router = APIRouter()


@router.post("/challenge")
async def challenge(challenge: Challenge):
    await make_challenge([challenge.challenger, challenge.challenged])
    return challenge


@router.get("/users")
async def user_list():
    return JSONResponse({'users': list(manager.connections.keys())})
