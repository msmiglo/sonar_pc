
from modules.abstract.abstract_display import AbstractDisplay
from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample
)


class History:
    def __init__(self):
        self.history = []

    def store(self, sample: AbstractSample):
        pass

    def get(self, i) -> AbstractSample:
        pass

    def get_last(self) -> AbstractSample:
        pass


class Result:
    def __init__(self, distance: float, metadata: dict):
        self.distance = distance
        self.metadata = metadata

    def to_string_1(self) -> str:
        pass

    def to_string_2(self) -> str:
        pass

    def to_string_3(self) -> str:
        pass


class Measurer:
    def __init__(self, factory: AbstractFactory):
        self._emitter = factory.create_emitter()
        self._receiver = factory.create_receiver()
        if not isinstance(self._emitter, AbstractEmitter):
            raise TypeError(
                "please provide Emitter class based on `modules."
                "abstract.abstract_factory.AbstractEmitter` interface")
        if not isinstance(self._receiver, AbstractReceiver):
            raise TypeError(
                "please provide Receiver class based on `modules."
                "abstract.abstract_factory.AbstractReceiver` interface")

        pass

    def check(self):
        pass

    def single_measurement(self) -> AbstractSample:
        pass

    def _emit_beep(self):
        pass

    def _get_response(self) -> AbstractSample:
        pass


class Controller:
    def __init__(self, factory: AbstractFactory, display: AbstractDisplay):
        self.measurer = Measurer(factory)
        self.history = History()
        self.factory = factory
        self.processor = factory.create_processor()
        self.display = display

    def loop(self, limit: int=None):
        pass

    def _step(self):
        pass

    def _measure(self) -> AbstractSample:
        pass

    def _process(self, sample: AbstractSample) -> Result:
        pass

    def _print(self, result: Result):
        pass
