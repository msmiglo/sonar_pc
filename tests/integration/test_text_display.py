
import unittest
from unittest.mock import patch

from modules.concrete.display import TextDisplay
from modules.core import Result


class TestDisplayIntegration(unittest.TestCase):
    def setUp(self):
        self.display = TextDisplay()
        self.reliable_args = (10.5, {"intensity": 5.0, "noise": 14.189})
        self.unreliable_args = (1.2, {"intensity": 1.5, "noise": 325})

    @patch('builtins.print')
    def test_display_with_reliable_result(self, mock_print):
        res = Result(*self.reliable_args)
        self.display.print(res)

        expected = ("Distance measured:\n\t10.50 m\tintensity: 5.00\n\n"
                    "noise background: 14.189")
        mock_print.assert_called_with(expected)

    @patch('builtins.print')
    def test_display_with_unreliable_result(self, mock_print):
        res = Result(*self.unreliable_args)
        self.display.print(res)

        expected = ("Distance measured:\n\t[1.20 m\tintensity: 1.50]"
                    " - not reliable\n\n"
                    "noise background: 325")
        mock_print.assert_called_with(expected)


if __name__ == '__main__':
    unittest.main()
