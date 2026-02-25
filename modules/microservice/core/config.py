
from types import SimpleNamespace as SNS


SETTINGS = SNS(
    EMITTER = SNS(
        BIND_HOST = "0.0.0.0",
        HOST = "127.0.0.1",
        PORT = 8001
    ),
    RECEIVER = SNS(
        BIND_HOST = "0.0.0.0",
        HOST = "127.0.0.1",
        PORT = 8002
    ),
)
