
import unittest
from unittest.mock import patch

from modules.concrete.display import TextDisplay
from modules.core import Result


class _ProcessorNoiseError(Exception): pass


class TestTextDisplayIntegration(unittest.TestCase):
    def setUp(self):
        self.display = TextDisplay()

    @patch('builtins.print')
    def test_display_no_data(self, mock_print):
        args = {"peaks": [], "noise": 1, "snr": 5.5555}
        expected = ("Distance:\n"
                    "\t[no data]\n"
                    "\n"
                    "background noise: 1.00\n"
                    "signal-to-noise ratio: 5.6")

        res = Result(**args)
        self.display.print(res)
        mock_print.assert_called_with(expected, flush=True)

    @patch('builtins.print')
    def test_display_with_reliable_result(self, mock_print):
        args = {"peaks": [(14, 50)], "noise": 134.4789,
                "snr": 100}
        expected = ("Distance:\n"
                    "\t14.00 m\tintensity: 50.00\n"
                    "\n"
                    "background noise: 134.48\n"
                    "signal-to-noise ratio: 100.0")

        res = Result(**args)
        self.display.print(res)
        mock_print.assert_called_with(expected, flush=True)

    @patch('builtins.print')
    def test_display_with_unreliable_result(self, mock_print):
        args = {"peaks": [(4.855, 2.03), (2.171, 1.45)], "noise": 1000 / 13,
                "snr": 43.777777}
        expected = ("Distance:\n"
                    "\t[2.17 m\tintensity: 1.45] - unreliable\n"
                    "\t[4.86 m\tintensity: 2.03] - unreliable\n"
                    "\n"
                    "background noise: 76.92\n"
                    "signal-to-noise ratio: 43.8")

        res = Result(**args)
        self.display.print(res)
        mock_print.assert_called_with(expected, flush=True)

    @patch('builtins.print')
    def test_display_with_error_result(self, mock_print):
        args = {"peaks": [(14, 50)], "noise": 134.4789, "snr": 100}
        error = _ProcessorNoiseError("too noisy data, main pulse lost")
        expected = ("Distance:\n"
                    "\t14.00 m\tintensity: 50.00\n"
                    "\n"
                    "background noise: 134.48\n"
                    "signal-to-noise ratio: 100.0\n"
                    "\n"
                    "[ERROR] _ProcessorNoiseError: too noisy data, "
                        "main pulse lost")

        res = Result.from_error(error, **args)
        self.display.print(res)
        mock_print.assert_called_with(expected, flush=True)


if __name__ == '__main__':
    unittest.main()
