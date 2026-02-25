
import time
import unittest

from modules.abstract.abstract_display import AbstractDisplay
from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample
)
from modules.core import Controller, Result


# ====================
# == HELPER CLASSES ==
# ====================


class Logger:
    def __init__(self):
        self.log_record = []

    def log(self, text):
        self.log_record.append((time.perf_counter(), text))


class _LogginBase:
    @classmethod
    def set_logger(cls, logger):
        cls.logger = logger

    @classmethod
    def log(cls, *args):
        cls.logger.log(*args)


# ======================
# == CONCRETE CLASSES ==
# ======================


class FakeSample(AbstractSample):
    def __init__(self):
        pass


class FakeDisplay(AbstractDisplay, _LogginBase):
    def __init__(self):
        pass

    def print(self, result):
        self.log("result printed.")


class FakeEmitter(AbstractEmitter, _LogginBase):
    def __init__(self, config):
        pass

    def check(self):
        self.logger.log("check completed.")

    def emit_beep(self):
        time.sleep(0.019)
        self.logger.log("playing started...")
        time.sleep(0.032)
        self.logger.log("playing stopped.")


class FakeReceiver(AbstractReceiver, _LogginBase):
    def __init__(self, config):
        pass

    def check(self):
        self.logger.log("check completed.")

    def record_signal(self):
        self.logger.log("recording started...")
        time.sleep(0.092)
        self.logger.log("recording stopped.")
        return FakeSample()


class FakeProcessor(AbstractProcessor):
    def __init__(self, config):
        pass

    def process(self, sample):
        return Result([(10, 5)], 897.1, 42)


class FakeFactory(AbstractFactory, _LogginBase):
    def __init__(self, config):
        pass

    def create_emitter(self):
        self.logger.log("emitter created.")
        return FakeEmitter({})

    def create_receiver(self):
        self.logger.log("receiver created.")
        return FakeReceiver({})

    def create_processor(self):
        self.logger.log("processor created.")
        return FakeProcessor({})

    def check(self):
        pass


# ================
# == TEST CASES ==
# ================


class TestMain(unittest.TestCase):
    def setUp(self):
        self.logger = Logger()
        FakeFactory.set_logger(self.logger)
        FakeDisplay.set_logger(self.logger)
        FakeEmitter.set_logger(self.logger)
        FakeReceiver.set_logger(self.logger)

    def test_whole(self):
        n = 5
        factory = FakeFactory({})
        display = FakeDisplay()
        ctrl = Controller(factory=factory, display=display)
        ctrl.loop(limit=n)

        logging_texts = [rec[1] for rec in self.logger.log_record]
        expected = [
            "emitter created.", "receiver created.", "processor created.",
            "check completed.", "check completed."
        ] + n * [
            "recording started...", "playing started...",
            "playing stopped.", "recording stopped.", "result printed."
        ]
        if not logging_texts == expected:
            for log in self.logger.log_record:
                print(log)
                if "result" in log[1]:
                    print()
        self.assertListEqual(logging_texts, expected)


if __name__ == '__main__':
    unittest.main()
