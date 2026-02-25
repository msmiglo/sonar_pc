
import unittest
from unittest.mock import MagicMock, patch

from modules.utilities import \
     _timestamp_to_ns, compute_latency, get_timestamp, wait_till_time


class TestTimestampToNs(unittest.TestCase):
    """
    test cases include:
    - test wrong input int
    - test wrong input str format
    - test ancient time to minus values
    - test normal, assert int result
    """
    def test_wrong_input_int(self):
        with self.assertRaises(AttributeError):
            _timestamp_to_ns(123456789)

    def test_wrong_input_str_format(self):
        with self.assertRaises(ValueError):
            _timestamp_to_ns("2023-10-10T10:10:10")

    def test_ancient_time(self):
        ancient_ts = "1900-01-01T01:01:05.000050000"
        with self.assertRaises(OSError):
            result = _timestamp_to_ns(ancient_ts)

    def test_normal_case(self):
        ts = "2023-10-10T10:10:10.500000000"
        result = _timestamp_to_ns(ts)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 1696925410500000000)


class TestGetTimestamp(unittest.TestCase):
    """
    patch time
    test cases include:
    - test no latency
    - test latency
    - test latency 1 ns
    """
    @patch('modules.utilities.time')
    def test_get_timestamp_no_latency(self, mock_time):
        mock_time.time_ns.return_value = 1000000000000000000
        result = get_timestamp(latency_s=0.0)
        mock_time.time_ns.assert_called_once_with()
        result2 = get_timestamp(latency_s=0.0)
        self.assertEqual(result, result2)
        # NOTE: probably this depends on timezone, might need correction
        self.assertEqual(result, "2001-09-09T03:46:40.000000000")

    @patch('modules.utilities.time')
    def test_get_timestamp_with_latency(self, mock_time):
        mock_time.time_ns.return_value = 1000000000700000000
        result = get_timestamp(latency_s=1.5)
        # NOTE: probably this depends on timezone, might need correction
        self.assertEqual(result, "2001-09-09T03:46:42.200000000")

    @patch('modules.utilities.time')
    def test_get_timestamp_1ns_latency(self, mock_time):
        mock_time.time_ns.return_value = 1000000000700000000
        result = get_timestamp(latency_s=0.000000001)
        # NOTE: probably this depends on timezone, might need correction
        self.assertEqual(result, "2001-09-09T03:46:40.700000001")


class TestComputeLatency(unittest.TestCase):
    """
    patch time, patch timestamp_to_ns
    test cases include:
    - test same minus same
    - test error side effect
    """
    @patch('modules.utilities.time')
    @patch('modules.utilities._timestamp_to_ns')
    def test_same_time_latency(self, mock_to_ns, mock_time):
        mock_time.time_ns.return_value = 2000000000000000000
        mock_to_ns.return_value = 2000000000000000000
        result = compute_latency("mock_time_stamp")
        self.assertEqual(result, 0.0)

    @patch('modules.utilities.time')
    @patch('modules.utilities._timestamp_to_ns')
    def test_latency_error_side_effect(self, mock_to_ns, mock_time):
        mock_to_ns.side_effect = ValueError("Format error")
        with self.assertRaises(ValueError):
            compute_latency("bad_format")


class TestWaitTillTime(unittest.TestCase):
    """
    patch time, patch timestamp_to_ns
    test cases include:
    - test minus value return
    - test normal value sleep
    """
    @patch('modules.utilities.time')
    @patch('modules.utilities._timestamp_to_ns')
    def test_wait_past_time(self, mock_to_ns, mock_time):
        current_time = 1000
        scheduled_time = 500
        mock_time.time_ns.return_value = current_time
        mock_to_ns.return_value = scheduled_time
        wait_till_time("mock_past_timestamp")
        mock_time.sleep.assert_not_called()

    @patch('modules.utilities.time')
    @patch('modules.utilities._timestamp_to_ns')
    def test_wait_future_time(self, mock_to_ns, mock_time):
        current_time = 1_000_000_000
        scheduled_time = 2_000_000_000
        mock_time.time_ns.return_value = 1_000_000_000
        mock_to_ns.return_value = 2_000_000_000
        wait_till_time("mock_future_timestamp")
        mock_time.sleep.assert_called_once_with(1.0)


if __name__ == '__main__':
    unittest.main()
