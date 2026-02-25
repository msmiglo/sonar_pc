
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class HealthErrorResponse(BaseModel):
    error_name: str
    error_message: str


class LatencyRequest(BaseModel):
    trigger_timestamp: str


class LatencyResponse(BaseModel):
    latency_s: float


class PlayRequest(BaseModel):
    schedule: str


class RecordRequest(BaseModel):
    schedule: str
