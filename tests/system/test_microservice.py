
from modules.concrete.text_display import TextDisplay
from modules.concrete.http_caller import HttpFactory
from modules.core import Controller


def test_http_caller():
    factory = HttpFactory({})
    display = TextDisplay()
    ctrl = Controller(factory=factory, display=display)
    ctrl.loop(limit=10)


def test():
    test_http_caller()


if __name__ == '__main__':
    test()
