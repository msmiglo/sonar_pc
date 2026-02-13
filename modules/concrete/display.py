
from modules.abstract.abstract_display import AbstractDisplay


class TextDisplay(AbstractDisplay):
    def __init__(self, config: dict=None):
        if config is None:
            config = {}
        self.config = config

    def print(self, result):
        print(results)
