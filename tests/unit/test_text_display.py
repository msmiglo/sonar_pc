
import unittest
from unittest.mock import MagicMock, patch

from modules.abstract.abstract_display import AbstractDisplay
from modules.concrete.display import TextDisplay


class TestTextDisplay(unittest.TestCase):
    """
    test cases include:
    - test creation
    - test printing None
    - test printing empty data
    - test printing one peak
    - test printing unreliable
    - test printing many peaks
    - test printing error
    """
    @staticmethod
    def _make_mock_peak(**data):
        mock_peak = {
            "distance": 1/7,
            "intensity": 14.789789,
            "reliable": True,
        }
        mock_peak.update(data)
        return mock_peak
        

    @staticmethod
    def _make_mock_result(**expected_dict):
        mock_dict = {
            "peaks": [],
            "noise": 114.83999999,
            "snr": 48.7894,
            "error": None
        }
        mock_dict.update(expected_dict)
        mock_result = MagicMock()
        mock_result.to_dict.return_value = mock_dict
        return mock_result

    def setUp(self):
        self.display = TextDisplay()
        self.weak_peak = self._make_mock_peak(intensity=1.23, reliable=False)
        self.peak_1 = self._make_mock_peak(distance=2.5)
        self.peak_2 = self._make_mock_peak(distance=5, intensity=45)

    def test_creation(self):
        self.assertIsInstance(self.display, AbstractDisplay)
        self.assertEqual(self.display.config, {})

    def test_printing_none(self):
        with self.assertRaises(AttributeError):
            self.display.print(None)

    @patch('builtins.print')
    def test_printing_empty_data(self, mock_print):
        mock_result = self._make_mock_result()
        self.display.print(mock_result)
        expected = ("Distance:\n"
                    "\t[no data]\n"
                    "\n"
                    "background noise: 114.84\n"
                    "signal-to-noise ratio: 48.8")
        mock_print.assert_called_once_with(expected, flush=True)

    @patch('builtins.print')
    def test_print_one_peak(self, mock_print):
        mock_result = self._make_mock_result(peaks=[self.peak_1])
        self.display.print(mock_result)
        expected = ("Distance:\n"
                    "\t2.50 m\tintensity: 14.79\n"
                    "\n"
                    "background noise: 114.84\n"
                    "signal-to-noise ratio: 48.8")
        mock_print.assert_called_with(expected, flush=True)

    @patch('builtins.print')
    def test_print_unreliable(self, mock_print):
        mock_result = self._make_mock_result(peaks=[self.weak_peak])
        self.display.print(mock_result)
        expected = ("Distance:\n"
                    "\t[0.14 m\tintensity: 1.23] - unreliable\n"
                    "\n"
                    "background noise: 114.84\n"
                    "signal-to-noise ratio: 48.8")
        mock_print.assert_called_once_with(expected, flush=True)

    @patch('builtins.print')
    def test_print_many_peaks(self, mock_print):
        mock_result = self._make_mock_result(
            peaks=[self.weak_peak, self.peak_1, self.peak_2])
        self.display.print(mock_result)
        expected = ("Distance:\n"
                    "\t[0.14 m\tintensity: 1.23] - unreliable\n"
                    "\t2.50 m\tintensity: 14.79\n"
                    "\t5.00 m\tintensity: 45.00\n"
                    "\n"
                    "background noise: 114.84\n"
                    "signal-to-noise ratio: 48.8")
        mock_print.assert_called_once_with(expected, flush=True)

    @patch('builtins.print')
    def test_print_error(self, mock_print):
        mock_result = self._make_mock_result(
            noise=0., snr=0., error="SomeError: error message")
        self.display.print(mock_result)
        expected = ("Distance:\n"
                    "\t[0.00 m\tintensity: 0.00] - unreliable\n"
                    "\n"
                    "background noise: 0.00\n"
                    "signal-to-noise ratio: 0.0\n"
                    "\n"
                    "[ERROR] SomeError: error message")
        mock_print.assert_called_once_with(expected, flush=True)


if __name__ == '__main__':
    unittest.main()
