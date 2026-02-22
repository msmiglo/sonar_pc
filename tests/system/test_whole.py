
"""
These are not considered an acceptance test as they do not have
the ability to check the IO performance. They are just the End-To-End
system checks.

These checks would need to perform full code deployment to
other devices - which requires the build of test environment.
"""


import unittest
from unittest.mock import patch

from modules.concrete.display import TextDisplay
from modules.concrete.pc_sound import PcFactory
from modules.core import Controller


class TestPcSound(unittest.TestCase):
    def setUp(self):
        pass

    @patch("modules.concrete.pc_sound.RECORDING_MARGIN_SECONDS", 0.280)
    @patch("modules.concrete.pc_sound.PLAY_DELAY_SECONDS", 0)
    @patch("modules.concrete.pc_sound.PLAYING_DURATION_SECONDS", 15 / 1000)
    def test_whole(self):
        factory = PcFactory({})
        display = TextDisplay()
        ctrl = Controller(factory=factory, display=display)
        ctrl.loop(limit=5)


'''class TestRadioDevices(unittest.TestCase):
    def setUp(self):
        pass

    def test_whole(self):
        factory = RadioFactory({})
        display = SmartphoneDisplay()
        ctrl = Controller(factory=factory, display=display)
        ctrl.loop(limit=10)'''


if __name__ == '__main__':
    unittest.main()
