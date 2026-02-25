
import os

from fastapi import FastAPI, Request
import uvicorn

from modules.concrete.pc_sound import PcFactory
from modules.microservice.api import (
    routes_common, routes_emitter, routes_receiver)
from modules.microservice.core.config import SETTINGS


SERVICE_TYPE = os.getenv("SERVICE_TYPE", "")


if SERVICE_TYPE not in ["EMITTER", "RECEIVER"]:
    raise RuntimeError ("please set correct env variable: SERVICE_TYPE")


async def lifespan(app: FastAPI):
    factory = PcFactory({})

    app.state.service_type = SERVICE_TYPE
    if SERVICE_TYPE == "EMITTER":
        emitter = factory.create_emitter()
        app.state.emitter = emitter
    elif SERVICE_TYPE == "RECEIVER":
        receiver = factory.create_receiver()
        app.state.receiver = receiver

    yield


def main():
    app = FastAPI(lifespan=lifespan)
    app.include_router(routes_common.router)
    if SERVICE_TYPE == "EMITTER":
        app.include_router(routes_emitter.router)
        host = SETTINGS.EMITTER.BIND_HOST
        port = SETTINGS.EMITTER.PORT
    elif SERVICE_TYPE == "RECEIVER":
        app.include_router(routes_receiver.router)
        host = SETTINGS.RECEIVER.BIND_HOST
        port = SETTINGS.RECEIVER.PORT

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        reload=True
    )

    server = uvicorn.Server(config)
    app.state.server = server
    server.run()


if __name__ == "__main__":
    main()
