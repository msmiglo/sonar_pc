
from modules.abstract.abstract_display import AbstractDisplay


class TextDisplay(AbstractDisplay):
    def __init__(self, config: dict=None):
        if config is None:
            config = {}
        self.config = config

    def print(self, result):
        txt = result.to_string_1()
        txt = (
            f"Distance measured:\n"
            f"{txt}\n"
            f"\n"
            f"noise background: {result.metadata['noise']}"
        )
        print(txt)
