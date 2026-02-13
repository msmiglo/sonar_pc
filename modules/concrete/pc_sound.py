
from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample
)
from modules.core import Result


class PcSample(AbstractSample):
    def __init__(self):
        pass


class PcEmitter(AbstractEmitter):
    def __init__(self, config):
        pass

    def check(self):
        pass

    def emit_beep(self):
        pass


class PcReceiver(AbstractReceiver):
    def __init__(self, config):
        pass

    def check(self):
        pass

    def record_signal(self) -> PcSample:
        pass


class PcProcessor(AbstractProcessor):
    def __init__(self, config):
        pass

    def process(self, sample: PcSample) -> Result:
        pass


class PcFactory(AbstractFactory):
    def __init__(self, config):
        pass

    def create_emitter(self) -> PcEmitter:
        pass

    def create_receiver(self) -> PcReceiver:
        pass

    def create_processor(self) -> PcProcessor:
        pass

    def check(self):
        pass
