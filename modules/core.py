
import threading

from modules.abstract.abstract_display import AbstractDisplay
from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample
)


class History:
    def __init__(self):
        self.history = []

    def store(self, sample: AbstractSample):
        self.history.append(sample)

    def get(self, i) -> AbstractSample:
        return self.history[i]

    def get_last(self) -> AbstractSample:
        return self.history[-1]


class Result:
    def __init__(self, distance: float, metadata: dict):
        self.distance = distance
        self.metadata = metadata

    def to_string_1(self) -> str:
        intensity = self.metadata["intensity"]
        txt = f"{self.distance:.02f} m\tintensity: {intensity:.02f}"
        if intensity <= 2:
            txt = f"[{txt}] - not reliable"
        txt = "\t" + txt
        return txt

    def to_string_2(self) -> str:
        pass

    def to_string_3(self) -> str:
        return "lalalala"


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

        self.barrier = threading.Barrier(2)

        # TODO - MAYBE SOME CALLIBRATION SOMEWHERE

    def check(self):
        self._emitter.check()
        self._receiver.check()

    def single_measurement(self) -> AbstractSample:
        t = threading.Thread(target=self._emit_beep)
        t.start()
        sample = self._get_response()
        t.join()
        return sample

    def _emit_beep(self):
        self.barrier.wait(timeout=5)
        self._emitter.emit_beep()

    def _get_response(self) -> AbstractSample:
        self.barrier.wait(timeout=5)
        sample = self._receiver.record_signal()
        return sample


class Controller:
    def __init__(self, factory: AbstractFactory, display: AbstractDisplay):
        self.measurer = Measurer(factory)
        self.history = History()
        self.factory = factory
        self.processor = factory.create_processor()
        self.display = display

        self.loop_event = threading.Event()

        self.measurer.check()

    def loop(self, limit: int=None):
        count = 0
        while not self.loop_event.is_set():
            self._step()
            count += 1
            if limit is not None and count >= limit:
                break

    def _step(self):
        sample = self._measure()
        self.history.store(sample)
        latest_sample = self.history.get_last()
        result = self._process(sample)
        self._print(result)

    def _measure(self) -> AbstractSample:
        sample = self.measurer.single_measurement()
        return sample

    def _process(self, sample: AbstractSample) -> Result:
        result = self.processor.process(sample)
        return result

    def _print(self, result: Result):
        self.display.print(result)
