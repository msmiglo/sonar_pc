
from abc import ABC, abstractmethod


class AbstractSample(ABC):
    pass


class AbstractEmitter(ABC):
    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def emit_beep(self):
        pass


class AbstractReceiver(ABC):
    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def record_signal(self) -> AbstractSample:
        pass


class AbstractProcessor(ABC):
    @abstractmethod
    def process(self, sample: AbstractSample):
        pass


class AbstractFactory(ABC):
    @abstractmethod
    def create_emitter(self) -> AbstractEmitter:
        pass

    @abstractmethod
    def create_receiver(self) -> AbstractReceiver:
        pass

    @abstractmethod
    def create_processor(self) -> AbstractProcessor:
        pass

    @abstractmethod
    def check(self):
        pass
