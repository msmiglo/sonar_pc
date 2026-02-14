
import unittest
from unittest.mock import MagicMock

from modules.abstract.abstract_display import AbstractDisplay
from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample
)
from modules.core import Controller, History, Measurer, Result


class FakeSample(AbstractSample):
    def __init__(self):
        pass


class FakeDisplay(AbstractSample):
    def __init__(self):
        self.txt_value = None

    def print(self, result):
        txt = result.to_string_1()
        self.txt_value = txt
        txt = result.to_string_3()
        return txt


class TestControllerStep(unittest.TestCase):
    def setUp(self):
        self.mock_measurer = MagicMock(spec=Measurer)
        self.mock_history = MagicMock(spec=History)
        self.mock_processor = MagicMock(spec=AbstractProcessor)
        self.mock_display = FakeDisplay()
        self.mock_result = MagicMock(spec=Result)
        self.fake_sample = FakeSample()

        self.mock_measurer.single_measurement.return_value = self.fake_sample
        self.mock_history.get_last.return_value = self.fake_sample
        self.mock_processor.process.return_value = self.mock_result

        self.ctrl = Controller.__new__(Controller)
        self.ctrl.measurer = self.mock_measurer
        self.ctrl.history = self.mock_history
        self.ctrl.processor = self.mock_processor
        self.ctrl.display = self.mock_display

    def test_sequence(self):
        self.ctrl._step()
        self.mock_measurer.single_measurement.assert_called_once()
        self.mock_history.store.assert_called_once_with(self.fake_sample)
        self.mock_history.get_last.assert_called_once_with()
        self.mock_processor.process.assert_called_once_with(self.fake_sample)
        self.mock_result.to_string_1.assert_called_once()


class TestHistory(unittest.TestCase):
    def test_storage(self):
        fake_sample_1 = FakeSample()
        fake_sample_2 = FakeSample()
        history = History()
        self.assertEqual(len(history.history), 0)
        history.store(fake_sample_1)
        history.store(fake_sample_2)
        self.assertIs(history.get_last(), fake_sample_2)
        self.assertIs(history.get(0), fake_sample_1)
        self.assertEqual(len(history.history), 2)


class TestMeasurer(unittest.TestCase):
    def setUp(self):
        self.mock_emitter = MagicMock(spec=AbstractEmitter)
        self.mock_receiver = MagicMock(spec=AbstractReceiver)
        self.fake_sample = FakeSample()

        self.measurer = Measurer.__new__(Measurer)
        self.measurer._emitter = self.mock_emitter
        self.measurer._receiver = self.mock_receiver
        self.measurer.barrier = MagicMock()

        self.mock_emitter.emit_beep.return_value = None
        self.mock_receiver.record_signal.return_value = self.fake_sample

    def test_measurement(self):
        result = self.measurer.single_measurement()
        self.mock_emitter.emit_beep.assert_called_once_with()
        self.mock_receiver.record_signal.assert_called_once_with()
        self.assertIs(result, self.fake_sample)


class TestDisplay(unittest.TestCase):
    def test_result(self):
        mock_result = MagicMock(spec=Result)
        mock_result.to_string_3.return_value = "1410"
        # result = Result(distance=1/7, metadata={"intensity": 20.5444}) - to unit
        fake_display = FakeDisplay()
        result = fake_display.print(mock_result)
        mock_result.to_string_1.assert_called_once_with()
        mock_result.to_string_2.assert_not_called()
        mock_result.to_string_3.assert_called_once_with()
        self.assertEqual(result, "1410")


class FakeProcessor(AbstractProcessor):
    def process(self, sample):
        return Result(distance=1/7, metadata={"intensity": 20.5444})


class FakeFactory(AbstractFactory):
    def create_emitter(self): return MagicMock(spec=AbstractEmitter)
    def create_receiver(self): return MagicMock(spec=AbstractReceiver)
    def create_processor(self): return FakeProcessor()
    def check(self): pass


class TestFlow(unittest.TestCase):
    def setUp(self):
        self.fake_factory = FakeFactory()
        self.fake_display = FakeDisplay()
        self.ctrl = Controller(self.fake_factory, self.fake_display)

    def test_initialization(self):
        self.ctrl.measurer._emitter.check.assert_called_once()
        self.ctrl.measurer._receiver.check.assert_called_once()
        self.assertEqual(len(self.ctrl.history.history), 0)

    def test_pipeline(self):
        fake_sample = FakeSample()
        self.ctrl.measurer._receiver.record_signal.return_value = fake_sample
        self.ctrl.loop(1)
        self.assertIs(self.ctrl.history.get_last(), fake_sample)
        self.assertEqual(self.fake_display.txt_value,
                         "\t0.14 m\tintensity: 20.54")
        self.ctrl.measurer._emitter.emit_beep.assert_called_once()
