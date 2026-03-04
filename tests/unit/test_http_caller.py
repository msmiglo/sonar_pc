
import unittest
from unittest.mock import MagicMock, patch

from modules.concrete.http_caller import (
    _BaseCaller, _validate_response, HttpEmitter, HttpFactory, HttpReceiver)
from modules.concrete.pc_sound import PcProcessor


class TestValidate(unittest.TestCase):
    @patch('builtins.print')
    def test_validate_response_ok(self, mock_print):
        mock_response = MagicMock()
        mock_response.ok = True
        _validate_response(mock_response)
        mock_print.assert_not_called()
        mock_response.json.assert_not_called()

    @patch('builtins.print')
    def test_validate_response_error(self, mock_print):
        mock_response = MagicMock()
        mock_response.ok = False
        _validate_response(mock_response)
        mock_print.assert_called()
        mock_response.json.assert_called_once_with()


class TestBaseCaller(unittest.TestCase):
    @patch('modules.concrete.http_caller._validate_response')
    @patch('modules.concrete.http_caller.requests')
    def test_check(self, mock_requests, mock_validate):
        # arrange
        mock_response = MagicMock()
        mock_requests.get.return_value = mock_response
        # act
        caller = _BaseCaller()
        caller.base_url = "http://test"
        caller.check()
        # assert
        mock_requests.get.assert_called_with("http://test/health")
        mock_validate.assert_called_with(mock_response)

    @patch('modules.concrete.http_caller.get_timestamp')
    def test_payload(self, mock_timestamp):
        mock_timestamp.return_value = "123.456"
        caller = _BaseCaller()
        caller.delay = 1.0
        payload = caller._payload()
        self.assertEqual(payload, {"schedule": "123.456"})
        mock_timestamp.assert_called_with(1.)


class TestHttpEmitter(unittest.TestCase):
    @patch('modules.concrete.http_caller.EMITTER_URL', 'test_url')
    def test_init(self):
        config = {"latency_s": 0.5}
        receiver = HttpEmitter(config)
        self.assertEqual(receiver.delay, 0.5)
        self.assertEqual(receiver.base_url, 'test_url')

    @patch('modules.concrete.http_caller._validate_response')
    @patch('modules.concrete.http_caller.requests')
    def test_emit_beep(self, mock_requests, mock_validate):
        # arrange
        mock_response = MagicMock()
        mock_requests.get.return_value = mock_response
        mock_emitter = MagicMock(spec=HttpEmitter)
        mock_emitter.delay = 0.5
        mock_emitter.base_url = "http://test"
        mock_emitter._payload.return_value = "fake_payload"

        # act
        result = HttpEmitter.emit_beep(mock_emitter)

        # assert
        self.assertIsNone(result)
        mock_requests.get.assert_called_once_with(
            "http://test/play", json="fake_payload")
        mock_validate.assert_called_with(mock_response)


class TestHttpReceiver(unittest.TestCase):
    @patch('modules.concrete.http_caller.RECEIVER_URL', 'test_url')
    def test_init(self):
        config = {"latency_s": 0.5}
        receiver = HttpReceiver(config)
        self.assertEqual(receiver.delay, 0.5)
        self.assertEqual(receiver.base_url, 'test_url')

    @patch('modules.concrete.http_caller._validate_response')
    @patch('modules.concrete.http_caller.requests')
    @patch('modules.concrete.http_caller.PcSample')
    def test_record_signal(self, mock_sample_cls, mock_requests, mock_validate):
        # arrange
        mock_response = MagicMock()
        mock_response.content = b"audio_data"
        mock_requests.get.return_value = mock_response
        mock_receiver = MagicMock(spec=HttpEmitter)
        mock_receiver.delay = 0.5
        mock_receiver.base_url = "http://test"
        mock_receiver._payload.return_value = "fake_payload"
        mock_sample = MagicMock()
        mock_sample_cls.from_data.return_value = mock_sample

        # act
        result = HttpReceiver.record_signal(mock_receiver)

        # assert
        mock_requests.get.assert_called_once_with(
            "http://test/record", json="fake_payload")
        mock_validate.assert_called_with(mock_response)
        self.assertIs(result, mock_sample)
        mock_sample_cls.from_data.assert_called_once_with(b"audio_data")


class TestHttpFactory(unittest.TestCase):
    @patch('modules.concrete.http_caller.HttpFactory._update_config')
    def test_factory_init(self, mock_update):
        config = {"a": 1}
        factory = HttpFactory(config)
        mock_update.assert_called_once_with()
        self.assertEqual(factory.config, config)

    @patch('modules.concrete.http_caller.requests')
    @patch('modules.concrete.http_caller.get_timestamp')
    def test_probe_latency(self, mock_ts, mock_requests):
        # arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"latency_s": 0.1}
        mock_requests.get.return_value = mock_response
        mock_ts.return_value = "timestamp"
        # act
        result = HttpFactory._probe_latency("http://test")
        # assert
        mock_ts.assert_called_once_with()
        mock_requests.get.assert_called_once_with(
            "http://test/latency", json={"trigger_timestamp": "timestamp"})
        self.assertEqual(result, 0.1)

    @patch('modules.concrete.http_caller.LATENCY_MARGIN_S', 0.01)
    def test_update_config(self):
        # arrange
        mock_factory = MagicMock(spec=HttpFactory)
        mock_factory.config = {}
        mock_factory._probe_latency.return_value = 0.1
        # act
        result = HttpFactory._update_config(mock_factory)
        # assert
        self.assertIn("latency_s", mock_factory.config)
        self.assertAlmostEqual(mock_factory.config["latency_s"], 0.12)
        mock_factory._probe_latency.assert_called()
        self.assertEqual(mock_factory._probe_latency.call_count, 8)
        self.assertIsNone(result)

    def test_create_methods(self):
        mock_factory = MagicMock(spec=HttpFactory)
        mock_factory.config = {"latency_s": 0.1}
        self.assertIsInstance(
            HttpFactory.create_emitter(mock_factory), HttpEmitter)
        self.assertIsInstance(
            HttpFactory.create_receiver(mock_factory), HttpReceiver)
        self.assertIsInstance(
            HttpFactory.create_processor(mock_factory), PcProcessor)


if __name__ == '__main__':
    unittest.main()
