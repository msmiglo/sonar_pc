
from abc import ABC, abstractmethod


class AbstractDisplay(ABC):
    @abstractmethod
    def print(self, result):
        pass
