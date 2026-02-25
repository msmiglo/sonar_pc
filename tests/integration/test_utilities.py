
from datetime import datetime
import time
import unittest
from unittest.mock import MagicMock, patch

from modules.utilities import \
     get_timestamp, compute_latency, wait_till_time, _timestamp_to_ns, TIMESTAMP_FORMAT


class TestTimestamps(unittest.TestCase):
    """
    test cases include:
    - test get timestamp compare to datetime now
    - test get latency after sleep
    - test wait 0.4 seconds
    - test wait -1.5 seconds
    """
    def setUp(self):
        self.delta = 0.05
        self.delay = 0.4

    def test_get_timestamp_now(self):
        time_now = get_timestamp()
        datetime_now = datetime.now().strftime(TIMESTAMP_FORMAT + ".%f")
        datetime_now = datetime_now + "000"

        time_ns = _timestamp_to_ns(time_now)
        datetime_ns = _timestamp_to_ns(datetime_now)
        main_part, fraction_part = time_now.split(".")

        self.assertEqual(len(fraction_part), 9)
        self.assertAlmostEqual(
            time_ns / 1e9, datetime_ns / 1e9, delta=self.delta)

    def test_get_latency_after_sleep(self):
        ts = get_timestamp()

        time.sleep(self.delay)

        latency = compute_latency(ts)
        self.assertAlmostEqual(latency, self.delay, delta=self.delta)

    def test_wait(self):
        target_ts = get_timestamp(latency_s=self.delay)

        start = time.time()
        wait_till_time(target_ts)
        end = time.time()

        elapsed = end - start
        self.assertAlmostEqual(elapsed, self.delay, delta=self.delta)

    def test_wait_schedule_from_past(self):
        past_ts = get_timestamp(latency_s=-1.5)

        start = time.time()
        wait_till_time(past_ts)
        end = time.time()

        elapsed = end - start
        self.assertLess(abs(elapsed), self.delta)


if __name__ == '__main__':
    unittest.main()
