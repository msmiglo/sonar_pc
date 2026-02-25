
import requests

from modules.abstract.abstract_factory import \
    AbstractEmitter, AbstractFactory, AbstractReceiver
from modules.concrete.pc_sound import PcProcessor, PcSample
from modules.core import Result
from modules.microservice.core.config import SETTINGS
from modules.utilities import get_timestamp


EMITTER_URL = f"http://{SETTINGS.EMITTER.HOST}:{SETTINGS.EMITTER.PORT}"
RECEIVER_URL = f"http://{SETTINGS.RECEIVER.HOST}:{SETTINGS.RECEIVER.PORT}"

HEALTH_ENDPOINT = "/health"
LATENCY_ENDPOINT = "/latency"
PLAY_ENDPOINT = "/play"
RECORD_ENDPOINT = "/record"

LATENCY_MARGIN_S = 0.030


def _validate_response(r):
    if not r.ok:
        print(f"wrong response: {r.status_code}: {r.reason}")
        print("--- ERROR: ---")
        try:
            print("Payload (JSON):", r.json())
        except ValueError:
            print("Payload (Text):", r.text[:200])


class _BaseCaller:
    def check(self):
        url = self.base_url + HEALTH_ENDPOINT
        response = requests.get(url)
        _validate_response(response)

    def _payload(self):
        schedule = get_timestamp(self.delay)
        payload = {"schedule": schedule}
        return payload


class HttpEmitter(_BaseCaller, AbstractEmitter):
    def __init__(self, config):
        self.delay = config["latency_s"]
        self.base_url = EMITTER_URL

    def emit_beep(self):
        url = self.base_url + PLAY_ENDPOINT
        response = requests.get(url, json=self._payload())
        _validate_response(response)


class HttpReceiver(_BaseCaller, AbstractReceiver):
    def __init__(self, config):
        self.delay = config["latency_s"]
        self.base_url = RECEIVER_URL

    def record_signal(self) -> PcSample:
        url = self.base_url + RECORD_ENDPOINT
        response = requests.get(url, json=self._payload())
        _validate_response(response)
        data = response.content
        return PcSample.from_data(data)


class HttpFactory(AbstractFactory):
    @staticmethod
    def _probe_latency(base_url):
        url = base_url + LATENCY_ENDPOINT
        timestamp = get_timestamp()
        payload = {"trigger_timestamp": timestamp}
        response = requests.get(url, json=payload)
        _validate_response(response)
        response_payload = response.json()
        latency_s = response_payload["latency_s"]
        return latency_s

    def _update_config(self):
        # make 4 rounds of measurements
        hosts = 4 * [EMITTER_URL, RECEIVER_URL]
        latencies = list(map(self._probe_latency, hosts))
        print("latencies:", latencies)
        # skip the first round
        latencies = latencies[2:]
        # set nominal delay
        latency_s = 1.1 * max(latencies) + LATENCY_MARGIN_S
        print("set up nominal value:", latency_s)
        print(flush=True)
        self.config["latency_s"] = latency_s

    def __init__(self, config):
        self.config = config
        self._update_config()

    def create_emitter(self) -> HttpEmitter:
        return HttpEmitter(self.config)

    def create_receiver(self) -> HttpReceiver:
        return HttpReceiver(self.config)

    def create_processor(self) -> PcProcessor:
        return PcProcessor({})

    def check(self):
        raise NotImplementedError("not used yet")
