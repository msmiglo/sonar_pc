
from datetime import datetime
import time


TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _timestamp_to_ns(timestamp):
    main_part, fraction_part = timestamp.split('.')
    dt = datetime.fromisoformat(main_part)
    seconds = dt.timestamp()
    seconds = int(seconds)

    nanoseconds = int(fraction_part)
    time_ns = seconds * 1_000_000_000 + nanoseconds
    return time_ns


def get_timestamp(latency_s=0.):
    now_ns = time.time_ns() + int(latency_s * 1e9)
    seconds = now_ns // 1_000_000_000
    nanoseconds = now_ns % 1_000_000_000

    dt = datetime.fromtimestamp(seconds)
    timestamp_txt = f"{dt.strftime(TIMESTAMP_FORMAT)}.{nanoseconds:09d}"
    return timestamp_txt


def compute_latency(timestamp):
    now_ns = time.time_ns()
    time_ns = _timestamp_to_ns(timestamp)
    latency_s = (now_ns - time_ns) / 1e9
    return latency_s


def wait_till_time(timestamp):
    scheduled_ns = _timestamp_to_ns(timestamp)
    now_ns = time.time_ns()
    if now_ns > scheduled_ns:
        return
    sleep_s = (scheduled_ns - now_ns) / 1e9
    time.sleep(sleep_s)
