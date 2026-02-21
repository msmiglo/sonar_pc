
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from modules.core import Controller, History, Measurer, Result
from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractReceiver, AbstractSample)


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.history = History()
        self.mock_sample = MagicMock()
        self.mock_sample2 = MagicMock()

    def test_creation_exists(self):
        self.assertIsInstance(self.history.history, list)

    def test_first_remains_first(self):
        self.history.store(self.mock_sample)
        self.history.store(self.mock_sample2)
        self.assertEqual(self.history.get(0), self.mock_sample)
        self.assertEqual(len(self.history.history), 2)

    def test_store(self):
        self.history.store(self.mock_sample)
        self.assertEqual(len(self.history.history), 1)

    def test_get(self):
        self.history.store(self.mock_sample)
        self.assertEqual(self.history.get(0), self.mock_sample)

    def test_get_last(self):
        self.history.store(self.mock_sample)
        self.history.store(self.mock_sample2)
        self.assertEqual(self.history.get_last(), self.mock_sample2)

    def test_storage_limit(self):
        history = History(limit=5)
        history.store(self.mock_sample)
        for _ in range(4):
            history.store(self.mock_sample2)
        self.assertEqual(len(history.history), 5)
        self.assertEqual(history.get(0), self.mock_sample)
        history.store(self.mock_sample)
        self.assertEqual(len(history.history), 5)
        self.assertEqual(history.get(0), self.mock_sample2)
        self.assertEqual(history.get_last(), self.mock_sample)


class TestResult(unittest.TestCase):
    def setUp(self):
        self.peak_1 = (1/7, 25.25655789)
        self.peak_2 = (6/7, 1.25655789)
        self.peak_3 = (1.8, 3)
        self.peak_numpy = (np.float64(1.8), np.float64(3))
        self.metadata = {"snr": 55, "noise": 871}
        self.error_output = "ZeroDivisionError: test error"

    def test_creation_empty(self):
        with self.assertRaises(TypeError):
            Result()

    def test_creation_no_data(self):
        with self.assertRaises(TypeError):
            r = Result(**self.metadata)

    def test_creation_ok(self):
        peaks = [self.peak_1]
        r = Result(peaks, **self.metadata)
        self.assertEqual(len(r.peaks), 1)
        self.assertAlmostEqual(r.peaks[0][0], 1/7)
        self.assertEqual(r.snr, self.metadata["snr"])
        self.assertEqual(r.metadata, {})

    def test_init_with_other_metadata(self):
        self.metadata["other"] = "other"
        r = Result([], **self.metadata)
        self.assertEqual(r.metadata, {"other": "other"})

    @staticmethod
    def _make_error():
        try:
            raise ZeroDivisionError("test error")
        except Exception as e:
            return e

    def test_from_error(self):
        e = self._make_error()
        r = Result.from_error(e)
        self.assertIsNotNone(r.error)
        self.assertEqual(len(r.peaks), 1)
        self.assertEqual(r.snr, 0.)
        self.assertEqual(r.noise, 0.)
        self.assertEqual(r.error, self.error_output)

    def test_no_peaks(self):
        peaks = []
        r = Result(peaks, **self.metadata)
        expected = {"peaks": [], "error": None}
        expected.update(self.metadata)
        self.assertEqual(r.to_dict(), expected)
        self.assertIsNone(r.error)

    def test_one_peak(self):
        peaks = [self.peak_1]
        r = Result(peaks, **self.metadata)
        expected = {
            "peaks": [
                {"distance": 1/7, "intensity": 25.25655789, "reliable": True}
            ],
            "error": None
        }
        expected.update(self.metadata)
        self.assertEqual(r.to_dict(), expected)
        self.assertIsNone(r.error)

    def test_not_reliable(self):
        peaks = [self.peak_2]
        r = Result(peaks, **self.metadata)
        data = r.to_dict()
        self.assertEqual(data["peaks"][0]["reliable"], False)
        self.assertIsNone(r.error)

    def test_peaks_sorting(self):
        peaks = [self.peak_3, self.peak_1, self.peak_2]
        r = Result(peaks, **self.metadata)
        self.assertListEqual(r.peaks, [self.peak_1, self.peak_2, self.peak_3])
        self.assertIsNone(r.error)

    def test_reliable_bool(self):
        peaks = [self.peak_numpy]
        res = Result(peaks, **self.metadata).to_dict()
        self.assertIsInstance(res["peaks"][0]["reliable"], bool)


class TestMeasurer(unittest.TestCase):
    def setUp(self):
        self.mock_factory = MagicMock(spec=AbstractFactory)
        self.mock_emitter = MagicMock(spec=AbstractEmitter)
        self.mock_receiver = MagicMock(spec=AbstractReceiver)

        self.mock_factory.create_emitter.return_value = self.mock_emitter
        self.mock_factory.create_receiver.return_value = self.mock_receiver
        self.measurer = Measurer(self.mock_factory)

    def test_init_validation(self):
        self.assertIsInstance(self.measurer._emitter, AbstractEmitter)
        self.assertIsInstance(self.measurer._receiver, AbstractReceiver)

    def test_check(self):
        self.measurer.check()
        self.mock_emitter.check.assert_called_once()
        self.mock_receiver.check.assert_called_once()

    def test_single_measurement_returns_sample(self):
        # Arrange expected sample from receiver
        expected_sample = MagicMock(spec=AbstractSample)
        self.mock_receiver.record_signal.return_value = expected_sample

        # Act
        result = self.measurer.single_measurement()

        # Assertions based on diagram relationships
        self.mock_emitter.emit_beep.assert_called_once()
        self.mock_receiver.record_signal.assert_called_once()
        self.assertEqual(result, expected_sample)

    def test_emit_beep_calls_emitter(self):
        # Arrange
        self.measurer.barrier = MagicMock()

        # Act
        self.measurer._emit_beep()

        # Assert
        self.mock_emitter.emit_beep.assert_called_once()

    def test_get_response_calls_receiver_record(self):
        # Arrange
        expected_sample = MagicMock(spec=AbstractSample)
        self.mock_receiver.record_signal.return_value = expected_sample
        self.measurer.barrier = MagicMock()

        # Act
        result = self.measurer._get_response()

        # Assert
        self.mock_receiver.record_signal.assert_called_once()
        self.assertEqual(result, expected_sample)


class TestController(unittest.TestCase):
    def setUp(self):
        self.mock_factory = MagicMock()
        self.mock_display = MagicMock()

        # Setup factory mocks
        self.mock_processor = MagicMock()
        self.mock_factory.create_processor.return_value = self.mock_processor

        # Patch History and Measurer used inside __init__
        with patch('modules.core.Measurer'), patch('modules.core.History'):
            self.controller = Controller(self.mock_factory, self.mock_display)

    # --- Creation Tests ---
    def test_init_sets_attributes(self):
        self.assertEqual(self.controller.factory, self.mock_factory)
        self.assertEqual(self.controller.display, self.mock_display)
        self.assertEqual(self.controller.processor, self.mock_processor)

    # --- Loop Method Tests ---
    def test_loop_respects_limit(self):
        self.controller._step = MagicMock()
        self.controller.loop(limit=3)
        self.assertEqual(self.controller._step.call_count, 3)

    def test_loop_stops_on_event(self):
        self.controller._step = MagicMock()
        self.controller.loop_event.set()
        self.controller.loop()
        self.controller._step.assert_not_called()

    # --- Step Method Tests ---
    def test_step_logic_flow(self):
        sample = MagicMock()
        result = MagicMock()
        self.controller._measure = MagicMock(return_value=sample)
        self.controller._process = MagicMock(return_value=result)
        self.controller._print = MagicMock()

        self.controller._step()

        self.controller.history.store.assert_called_with(sample)
        self.controller.history.get_last.assert_called_once()
        self.controller._print.assert_called_with(result)

    # --- Internal Method Tests & Errors ---
    def test_measure_calls_measurer(self):
        mock_sample = MagicMock()
        self.controller.measurer.single_measurement.return_value = mock_sample
        res = self.controller._measure()
        self.assertIs(res, mock_sample)

    def test_process_call(self):
        mock_sample = MagicMock()
        mock_result = MagicMock()
        self.controller.processor.process.return_value = mock_result
        result = self.controller._process(mock_sample)
        self.controller.processor.process.assert_called_once_with(mock_sample)
        self.assertIs(result, mock_result)

    def test_process_error_handling(self):
        self.controller.processor.process.side_effect = IOError(
            "Process Error")
        with self.assertRaises(IOError):
            self.controller._process(MagicMock())

    def test_print_calls_display(self):
        mock_result = MagicMock()
        self.controller._print(mock_result)
        self.mock_display.print.assert_called_with(mock_result)


if __name__ == '__main__':
    unittest.main()
