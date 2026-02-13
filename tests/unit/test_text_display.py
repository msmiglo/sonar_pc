
import unittest

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
        pass

    def test_creation(self):
        display = TextDisplay()
        self.assertIsInstance(display, AbstractDisplay)

    def test_printing_none(self):
        pass

    def test_printing_empty_data(self):
        pass

    def test_printing_actual_data(self):
        pass


if __name__ == '__main__':
    unittest.main()
