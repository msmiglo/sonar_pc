
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
    - test printing actual data
    """
    def setUp(self):
        self.display = TextDisplay()

    def test_creation(self):
        self.assertIsInstance(self.display, AbstractDisplay)

    def test_printing_none(self):
        with self.assertRaises(AttributeError):
            self.display.print(None)

    @patch('builtins.print')
    def test_printing_empty_data(self, mock_print):
        mock_result = MagicMock()
        mock_result.to_string_1.return_value = ""
        mock_result.metadata = {'noise': 0}

        self.display.print(mock_result)
        mock_print.assert_called_once()

    @patch('builtins.print')
    def test_printing_actual_data(self, mock_print):
        mock_result = MagicMock()
        mock_result.to_string_1.return_value = "10m"
        mock_result.metadata = {'noise': 'low'}

        self.display.print(mock_result)
        expected_output = "Distance measured:\n10m\n\nnoise background: low"
        mock_print.assert_called_with(expected_output)


if __name__ == '__main__':
    unittest.main()
