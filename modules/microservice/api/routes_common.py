
from typing import Union

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from modules.microservice.schemas import \
     HealthErrorResponse, HealthResponse, LatencyRequest, LatencyResponse
from modules.utilities import compute_latency


router = APIRouter()


def check_service(request_ref):
    if request_ref.app.state.service_type == "EMITTER":
        request_ref.app.state.emitter.check()
    if request_ref.app.state.service_type == "RECEIVER":
        request_ref.app.state.receiver.check()


@router.get(
    "/health",
    response_model=Union[HealthResponse, HealthErrorResponse],
    responses={
        200: {
            "description": "server works",
            "model": HealthResponse
        },
        503: {
            "description": "error on servers backend",
            "model": HealthErrorResponse
        }
    }
)
async def get_health(request: Request):
    try:
        check_service(request)
        return {"status": "ok"}
    except Exception as e:
        error_name = e.__class__.__name__
        error_message = str(e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error_name": error_name, "error_message": error_message}
        )


@router.get("/latency", response_model=LatencyResponse)
async def get_latency(request: Request, data: LatencyRequest):
    check_service(request)
    latency_s = compute_latency(data.trigger_timestamp)
    return {"latency_s": latency_s}


@router.get("/stop")
async def shut_down(request: Request):
    request.app.state.server.should_exit = True
    return Response(status_code=status.HTTP_204_NO_CONTENT)
