
from fastapi import APIRouter, Request, Response

from modules.microservice.schemas import RecordRequest
from modules.utilities import wait_till_time


router = APIRouter()


@router.get("/record")
async def record(request: Request, data: RecordRequest):
    wait_till_time(data.schedule)
    sample = request.app.state.receiver.record_signal()
    return Response(
        content=sample.to_data(),
        media_type="application/octet-stream"
    )
