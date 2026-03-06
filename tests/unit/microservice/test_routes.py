
import asyncio
import unittest
from unittest.mock import MagicMock, patch

from modules.microservice.api.routes_common import (
    check_service, shut_down, get_health, get_latency)
from modules.microservice.api.routes_emitter import play
from modules.microservice.api.routes_receiver import record


class TestEndpointFunctions(unittest.TestCase):
    """
    testing only python logic without integration
    """
    def setUp(self):
        self.mock_request = MagicMock()

    def test_check_service_emitter(self):
        # arrange
        mock_service = MagicMock()
        mock_service.app.state.service_type = "EMITTER"
        # act
        result = check_service(mock_service)
        # assert
        self.assertIsNone(result)
        mock_service.app.state.emitter.check.assert_called_once()
        mock_service.app.state.receiver.check.assert_not_called()

    def test_check_service_receiver(self):
        # arrange
        mock_service = MagicMock()
        mock_service.app.state.service_type = "RECEIVER"
        # act
        result = check_service(mock_service)
        # assert
        self.assertIsNone(result)
        mock_service.app.state.emitter.check.assert_not_called()
        mock_service.app.state.receiver.check.assert_called_once()

    @patch('modules.microservice.api.routes_common.check_service')
    def test_health(self, mock_check):
        response = asyncio.run(get_health(self.mock_request))
        mock_check.assert_called_once_with(self.mock_request)
        self.assertEqual(response, {"status": "ok"})

    @patch('modules.microservice.api.routes_common.JSONResponse')
    @patch('modules.microservice.api.routes_common.check_service')
    def test_not_health(self, mock_check, mock_response_cls):
        mock_check.side_effect = OSError("system error")

        response = asyncio.run(get_health(self.mock_request))

        mock_check.assert_called_once_with(self.mock_request)
        mock_response_cls.assert_called_once()
        self.assertIn("status_code", mock_response_cls.call_args[1])
        self.assertEqual(
            mock_response_cls.call_args[1]["content"],
            {"error_name": "OSError", "error_message": "system error"}
        )

    @patch('modules.microservice.api.routes_common.check_service')
    @patch('modules.microservice.api.routes_common.compute_latency')
    def test_latency(self, mock_latency, mock_check):
        # arrange
        mock_data = MagicMock()
        mock_data.trigger_timestamp = "mock_timestamp"
        mock_latency.return_value = 0.1
        # act
        response = asyncio.run(get_latency(self.mock_request, mock_data))
        # assert
        mock_check.assert_called_once_with(self.mock_request)
        mock_latency.assert_called_once_with("mock_timestamp")
        self.assertDictEqual(response, {"latency_s": 0.1})

    @patch('modules.microservice.api.routes_common.Response')
    def test_shutdown(self, mock_response_cls):
        response = asyncio.run(shut_down(self.mock_request))
        self.assertIs(self.mock_request.app.state.server.should_exit, True)
        self.assertIn("status_code", mock_response_cls.call_args[1])

    @patch('modules.microservice.api.routes_emitter.Response')
    @patch('modules.microservice.api.routes_emitter.wait_till_time')
    def test_play(self, mock_wait, mock_response_cls):
        # arrange
        mock_data = MagicMock()
        mock_data.schedule = "mock_timestamp"

        # act
        response = asyncio.run(play(self.mock_request, mock_data))

        # assert
        mock_wait.assert_called_once_with("mock_timestamp")
        self.mock_request.app.state.emitter.emit_beep.assert_called_once_with()
        mock_response_cls.assert_called_once()
        self.assertIn("status_code", mock_response_cls.call_args[1])

    @patch('modules.microservice.api.routes_receiver.Response')
    @patch('modules.microservice.api.routes_receiver.wait_till_time')
    def test_record(self, mock_wait, mock_response_cls):
        # arrange
        mock_data = MagicMock()
        mock_data.schedule = "mock_timestamp"
        mock_sample = MagicMock()
        self.mock_request.app.state.receiver.record_signal.return_value = \
            mock_sample
        mock_sample.to_data.return_value = b"sound_data"

        # act
        response = asyncio.run(record(self.mock_request, mock_data))

        # assert
        mock_wait.assert_called_once_with("mock_timestamp")
        self.mock_request.app.state.receiver.record_signal.assert_called_once()
        mock_response_cls.assert_called_once_with(
            content=b"sound_data", media_type="application/octet-stream")


if __name__ == '__main__':
    unittest.main()
