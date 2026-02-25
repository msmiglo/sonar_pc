
from fastapi import APIRouter, Request, Response, status

from modules.microservice.schemas import PlayRequest
from modules.utilities import wait_till_time


router = APIRouter()


@router.get("/play")
async def play(request: Request, data: PlayRequest):
    wait_till_time(data.schedule)
    request.app.state.emitter.emit_beep()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
