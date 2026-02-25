
import unittest
from unittest.mock import MagicMock, patch

from modules.microservice import schemas
from modules.microservice.core import config, security


class TestImports(unittest.TestCase):
    """
    limited tests - import and values
    """
    def test_config(self):
        config.SETTINGS.EMITTER.HOST
        config.SETTINGS.RECEIVER.BIND_HOST

    def test_schemas(self):
        schemas.HealthResponse
        schemas.LatencyRequest
        with self.assertRaises(AttributeError):
            schemas.NotExisting


if __name__ == '__main__':
    unittest.main()
