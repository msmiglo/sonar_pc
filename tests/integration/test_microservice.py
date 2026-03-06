
import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.microservice.api.routes_common import router as router_common
from modules.microservice.api.routes_emitter import router as router_emit
from modules.microservice.api.routes_receiver import router as router_rec


class TestCommon(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router_common)
        self.client = TestClient(self.app)

        self.app.state.service_type = "EMITTER"
        self.app.state.emitter = MagicMock()
        self.app.state.server = MagicMock()

    def test_get_health_success(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.app.state.emitter.check.assert_called_once()

    def test_get_health_failure(self):
        # arrange
        self.app.state.emitter.check.side_effect = Exception("Hardware failure")
        # act
        response = self.client.get("/health")
        # assert
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error_name"], "Exception")
        self.assertEqual(response.json()["error_message"], "Hardware failure")

    @patch("modules.utilities.time")
    def test_get_latency(self, mock_time):
        # arrange
        mock_time.time_ns.return_value = 1772753891456456456
        payload = {"trigger_timestamp": "2026-03-06T00:38:10.123123123"}
        # act
        response = self.client.request("GET", "/latency", json=payload)
        # assert
        mock_time.time_ns.assert_called_once_with()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"latency_s": 1.333333333})

    def test_shut_down(self):
        response = self.client.get("/stop")
        self.assertEqual(response.status_code, 204)
        self.assertIs(self.app.state.server.should_exit, True)


class TestSpecific(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router_emit)
        self.app.include_router(router_rec)
        self.client = TestClient(self.app)

        self.app.state.emitter = MagicMock()
        self.app.state.receiver = MagicMock()
        self.app.state.server = MagicMock()

        self.mock_time_value = 1772753891456456456
        self.payload = {"schedule": "2026-03-06T01:43:10.123123123"}

    @patch("modules.utilities.time")
    def test_play(self, mock_time):
        # arrange
        mock_time.time_ns.return_value = self.mock_time_value
        # act
        response = self.client.request("GET", "/play", json=self.payload)
        # assert
        self.assertEqual(response.status_code, 204)
        mock_time.time_ns.assert_called_once_with()
        self.app.state.emitter.emit_beep.assert_called_once_with()

    @patch("modules.utilities.time")
    def test_record(self, mock_time):
        # arrange
        mock_time.time_ns.return_value = self.mock_time_value
        fake_data = b"fake sound data"
        mock_sample = MagicMock()
        mock_sample.to_data.return_value = fake_data
        self.app.state.receiver.record_signal.return_value = mock_sample
        # act
        response = self.client.request("GET", "/record", json=self.payload)
        # assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, fake_data)
        self.assertEqual(response.headers["content-type"],
                         "application/octet-stream")
        mock_time.time_ns.assert_called_once_with()
        self.app.state.receiver.record_signal.assert_called_once()


if __name__ == '__main__':
    unittest.main()
