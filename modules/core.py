
import threading

from modules.abstract.abstract_display import AbstractDisplay
from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample
)


RELIABILITY_THRESHOLD = 2.5


class History:
    def __init__(self, limit=None):
        self.history = []
        self.limit = limit

    def store(self, sample: AbstractSample):
        self.history.append(sample)
        if self.limit is not None and len(self.history) > self.limit:
            self.history.pop(0)

    def get(self, i) -> AbstractSample:
        return self.history[i]

    def get_last(self) -> AbstractSample:
        return self.history[-1]


class Result:
    """
    Glossary:
    - main pulse - the original signal emitted by emitter
    - peaks - secondary peaks in the data - possibly reflections
    - noise - median value of wavelet transform matrix
    - snr - signal to noise ratio, snr = [main pulse height] / [noise]
    - intensity - reliability of signal depending on processing method
    """
    def __init__(self, peaks, noise, snr, **metadata):
        peaks = sorted(peaks, key=lambda p: p[0])
        self.peaks = list(peaks)
        self.noise = noise
        self.snr = snr
        self.metadata = metadata
        self.error = None

    @classmethod
    def from_error(cls, error, **kwargs):
        init_args = dict(peaks=[(0, 0)], noise=0, snr=0)
        init_args.update(kwargs)
        result = cls(**init_args)
        error_txt = f"{type(error).__name__}: {error}"
        result.error = error_txt
        return result

    def to_dict(self):
        peaks = [{
            "distance": p[0],
            "intensity": p[1],
            "reliable": bool(p[1] > RELIABILITY_THRESHOLD)
        } for p in self.peaks]
        return {
            "peaks": peaks,
            "noise": self.noise,
            "snr": self.snr,
            "error": self.error,
            "metadata": self.metadata
        }


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
