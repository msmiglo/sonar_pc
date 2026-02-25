
import unittest
from unittest.mock import ANY, call, MagicMock, patch

from modules.concrete.http_caller import HttpEmitter, HttpFactory, HttpReceiver
from modules.concrete.pc_sound import PcProcessor, PcSample
from modules.microservice.core.config import SETTINGS


class TestHttpEmitter(unittest.TestCase):
    def setUp(self):
        config = {"latency_s": 0.5}
        self.emitter = HttpEmitter(config)
        self.base_url = f"http://{SETTINGS.EMITTER.HOST}:{SETTINGS.EMITTER.PORT}"

    @patch('modules.concrete.http_caller.requests')
    def test_check(self, mock_requests):
        # arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_requests.get.return_value = mock_response
        # act
        self.emitter.check()
        # assert
        expected_url = self.base_url + "/health"
        mock_requests.get.assert_called_once_with(expected_url)

    @patch('modules.concrete.http_caller.requests')
    @patch('modules.concrete.http_caller.get_timestamp')
    def test_beep(self, mock_timestamp, mock_requests):
        # arrange
        fake_timestamp = "2023-10-10T10:10:10.000000000"
        mock_timestamp.return_value = fake_timestamp
        mock_response = MagicMock()
        mock_response.ok = True
        mock_requests.get.return_value = mock_response
        # act
        result = self.emitter.emit_beep()
        # assert
        self.assertIsNone(result)
        expected_url = self.base_url + "/play"
        expected_payload = {"schedule": fake_timestamp}
        mock_requests.get.assert_called_once_with(
            expected_url, json=expected_payload)
        mock_timestamp.assert_called_once_with(0.5)


class TestHttpReceiver(unittest.TestCase):
    def setUp(self):
        config = {"latency_s": 0.050}
        self.receiver = HttpReceiver(config)
        self.base_url = (f"http://{SETTINGS.RECEIVER.HOST}"
                         f":{SETTINGS.RECEIVER.PORT}")

    @patch('modules.concrete.http_caller.PcSample')
    @patch('modules.concrete.http_caller.get_timestamp')
    @patch('modules.concrete.http_caller.requests')
    def test_record_signal(self, mock_requests,
                           mock_timestamp, mock_sample_cls):
        # arrange
        fake_timestamp = "2024-01-01T12:00:00.000000000"
        mock_timestamp.return_value = fake_timestamp
        mock_sample = MagicMock()
        mock_sample_cls.from_data.return_value = mock_sample

        fake_binary_content = b'\x00\x01\x02\x03'
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = fake_binary_content
        mock_requests.get.return_value = mock_response

        mock_sample = MagicMock()
        mock_sample_cls.from_data.return_value = mock_sample

        # act
        sample = self.receiver.record_signal()

        # assert
        expected_url = self.base_url + "/record"
        expected_payload = {"schedule": fake_timestamp}
        mock_requests.get.assert_called_once_with(
            expected_url, json=expected_payload)

        mock_sample_cls.from_data.assert_called_once_with(fake_binary_content)
        self.assertIs(sample, mock_sample)
        mock_timestamp.assert_called_once_with(0.05)


class TestHttpFactory(unittest.TestCase):
    @patch('modules.concrete.http_caller.LATENCY_MARGIN_S', 0.05)
    @patch('modules.concrete.http_caller.get_timestamp')
    @patch('modules.concrete.http_caller.requests')
    def test_creations(self, mock_requests, mock_timestamp):
        # arrange
        mock_latency_measurements = [
            0.5, 0.6, 0.1, 0.12, 0.08, 0.09, 0.11, 0.10]
        mock_responses = []

        for latency_i in mock_latency_measurements:
            m = MagicMock()
            m.ok = True
            m.json.return_value = {"latency_s": latency_i}
            mock_responses.append(m)

        mock_requests.get.side_effect = mock_responses
        mock_timestamp.return_value = "mock_timestamp"

        # act
        factory = HttpFactory({})
        emitter = factory.create_emitter()
        receiver = factory.create_receiver()
        processor = factory.create_processor()

        # assert
        self.assertIsInstance(emitter, HttpEmitter)
        self.assertIsInstance(receiver, HttpReceiver)
        self.assertIsInstance(processor, PcProcessor)

        expected_latency = 1.1 * 0.12 + 0.05
        self.assertAlmostEqual(factory.config["latency_s"], expected_latency)
        self.assertEqual(mock_requests.get.call_count, 8)
        self.assertEqual(emitter.delay, expected_latency)
        self.assertEqual(receiver.delay, expected_latency)


class TestHttpModule(unittest.TestCase):
    def setUp(self):
        emitter_url = (f"http://{SETTINGS.EMITTER.HOST}"
                       f":{SETTINGS.EMITTER.PORT}")
        receiver_url = (f"http://{SETTINGS.RECEIVER.HOST}"
                        f":{SETTINGS.RECEIVER.PORT}")
        self.emitter_latency = emitter_url + "/latency"
        self.receiver_latency = receiver_url + "/latency"
        self.emitter_health = emitter_url + "/health"
        self.receiver_health = receiver_url + "/health"
        self.emitter_play = emitter_url + "/play"
        self.receiver_record = receiver_url + "/record"

    @patch('modules.concrete.http_caller.requests')
    def test_whole(self, mock_requests):
        # arrange
        fake_sound_data = (
            b"\x04\x00\x08\x00\t\x00\x14\x00\x06\x00\xff\xff\xf5"
            b"\xff\xfc\xff\xf7\xff\xf8\xff\xf2\xff\x05\x00\x00\x00"
        )
        mock_responses = []
        for _ in range(8):
            m = MagicMock()
            m.ok = True
            m.json.return_value = {"latency_s": 0.1}
            mock_responses.append(m)
        for _ in range(2):
            m = MagicMock()
            m.ok = True
            m.json.return_value = {"status": "ok"}
            mock_responses.append(m)

        m_play = MagicMock()
        m_play.ok = True
        mock_responses.append(m_play)

        m_rec = MagicMock()
        m_rec.ok = True
        m_rec.content = fake_sound_data
        mock_responses.append(m_rec)

        mock_requests.get.side_effect = mock_responses

        # act
        factory = HttpFactory({})
        emitter = factory.create_emitter()
        receiver = factory.create_receiver()
        processor = factory.create_processor()

        emitter.check()
        receiver.check()

        emitter.emit_beep()
        sample = receiver.record_signal()

        # assert
        self.assertIsInstance(emitter, HttpEmitter)
        self.assertIsInstance(receiver, HttpReceiver)
        self.assertIsInstance(processor, PcProcessor)
        self.assertIsInstance(sample, PcSample)
        self.assertEqual(fake_sound_data, sample.to_data())

        calibration_calls = 4 * [
            call(self.emitter_latency, json={"trigger_timestamp": ANY}),
            call(self.receiver_latency, json={"trigger_timestamp": ANY}),
        ]
        action_calls = [
            call(self.emitter_health),
            call(self.receiver_health),
            call(self.emitter_play, json={"schedule": ANY}),
            call(self.receiver_record, json={"schedule": ANY}),
        ]
        expected_calls = calibration_calls + action_calls
        mock_requests.get.assert_has_calls(expected_calls)


if __name__ == '__main__':
    unittest.main()
