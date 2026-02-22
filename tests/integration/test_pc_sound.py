
import random
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

import modules.concrete.pc_sound as pcs
from modules.concrete.pc_sound import (
    PcEmitter, PcFactory, PcProcessor, PcReceiver, PcSample, _Series, _Stripe)
from modules.concrete.pc_sound import (
    ProcessorEmptyDataError,
    ProcessorNoisyDataError,
    ProcessorNoPeaksDetectedError,
    ProcessorNoSoundError,
    ProcessorWrongFrequencyError
)
from modules.core import Result


class TestPcSample(unittest.TestCase):
    def setUp(self):
        self.signal = [1, -5, 6, 7, 100, 25, -15, 0, 3]

    def test_transformation(self):
        sample = PcSample.from_signal(self.signal).to_data()
        sample = PcSample.from_data(sample).to_values()
        sample = PcSample.from_values(sample).to_chunks()
        sample = PcSample.from_chunks(sample).to_signal()
        self.assertListEqual(list(sample), self.signal)


class TestPcEmitter(unittest.TestCase):
    def setUp(self):
        self.mock_stream = MagicMock()
        self.pa = MagicMock()
        self.pa.open.return_value = self.mock_stream
        self.emitter = PcEmitter({"pyaudio": self.pa})

    def test_check(self):
        self.emitter.check()
        self.mock_stream.write.assert_called_once_with(b"")

    def test_beep(self):
        # arrange
        mock_sound_signal = [random.randint(-2000, 3000) for i in range(10000)]
        mock_sound_chunks = PcSample.from_signal(mock_sound_signal).to_chunks()
        # act
        self.emitter.emit_beep()
        # assert
        self.mock_stream.write.assert_called()
        calls = self.mock_stream.write.call_args_list
        for args, kwargs in calls:
            self.assertIsInstance(args[0], bytes)
            self.assertDictEqual(kwargs, {})
        self.mock_stream.stop_stream.assert_called_once_with()
        self.mock_stream.close.assert_called_once_with()


class TestPcReceiver(unittest.TestCase):
    def setUp(self):
        self.mock_stream = MagicMock()
        self.pa = MagicMock()
        self.pa.open.return_value = self.mock_stream
        self.receiver = PcReceiver({"pyaudio": self.pa})

    def test_check(self):
        self.receiver.check()
        self.mock_stream.read.assert_called_once_with(0)

    def test_record(self):
        # arrange
        mock_sound_signal = [random.randint(-2000, 3000) for i in range(300)]
        mock_sound_data = PcSample.from_signal(mock_sound_signal).to_data()
        self.mock_stream.read.return_value = mock_sound_data
        # act
        sample = self.receiver.record_signal()
        # assert
        calls = self.mock_stream.read.call_args_list
        for args, kwargs in calls:
            self.assertIsInstance(args[0], int)
            self.assertDictEqual(kwargs, {})
        self.mock_stream.stop_stream.assert_called_once_with()
        self.mock_stream.close.assert_called_once_with()
        self.assertIsInstance(sample, PcSample)
        self.assertGreater(len(sample), 0)


class TestPcProcessor(unittest.TestCase):
    """
    test cases include:
    - test all errors
    - test happy path
    """
    def setUp(self):
        n = 20000
        self.noise_values = np.array(
            [random.random() - 0.5 for _ in range(n)])
        self.pulse_values = np.real(
            _Stripe._my_wavelet(n, pcs.CARRIER_FREQUENCY))

    def test_empty(self):
        sample = PcSample.from_signal([])
        proc = PcProcessor({})
        result = proc.process(sample)
        self.assertIsInstance(result, Result)
        self.assertIsInstance(result.error, str)
        self.assertIn(ProcessorEmptyDataError.__name__, result.error)

    def test_flat(self):
        sample = PcSample.from_signal(1000 * [600])
        proc = PcProcessor({})
        result = proc.process(sample)
        self.assertIsInstance(result, Result)
        self.assertIsInstance(result.error, str)
        self.assertIn(ProcessorNoSoundError.__name__, result.error)

    def test_wrong_freq(self):
        n, f = 2000, 0.003
        freq_values = 0.7 * np.sin(2 * np.pi * f * np.arange(n))
        sample = PcSample.from_values(freq_values)

        proc = PcProcessor({})
        result = proc.process(sample)
        self.assertIsInstance(result, Result)
        self.assertIsInstance(result.error, str)
        self.assertIn(ProcessorWrongFrequencyError.__name__, result.error)

    @patch("modules.concrete.pc_sound.SNR_THRESHOLD", 100)
    def test_noise(self):
        c = 0.5
        values = c * self.noise_values + (1 - c) * self.pulse_values
        sample = PcSample.from_values(values)

        proc = PcProcessor({})
        result = proc.process(sample)
        self.assertIsInstance(result, Result)
        self.assertIsInstance(result.error, str)
        self.assertIn(ProcessorNoisyDataError.__name__, result.error)

    def test_no_peak(self):
        c = 0.01
        values = c * self.noise_values + (1 - c) * self.pulse_values
        sample = PcSample.from_values(values)

        proc = PcProcessor({})
        result = proc.process(sample)
        self.assertIsInstance(result, Result)
        self.assertIsInstance(result.error, str)
        self.assertIn(ProcessorNoPeaksDetectedError.__name__, result.error)

    def test_process(self):
        shifted = np.roll(self.pulse_values, 500)
        values = 0.8 * self.pulse_values + 0.1 * shifted \
                 + 0.001 * self.noise_values
        sample = PcSample.from_values(values)

        proc = PcProcessor({})
        result = proc.process(sample)
        self.assertIsInstance(result, Result)
        self.assertIsNone(result.error)


class TestPcFactory(unittest.TestCase):
    @patch("modules.concrete.pc_sound.pyaudio")
    def test_creations(self, mock_pyaudio):
        factory = PcFactory({})
        emitter = factory.create_emitter()
        receiver = factory.create_receiver()
        processor = factory.create_processor()

        self.assertIsInstance(emitter, PcEmitter)
        self.assertIsInstance(receiver, PcReceiver)
        self.assertIsInstance(processor, PcProcessor)


class TestModule(unittest.TestCase):
    @patch("modules.concrete.pc_sound.pyaudio")
    def test_whole(self, mock_pyaudio_mdl):
        # arrange
        mock_stream = MagicMock()
        mock_pyaudio = MagicMock()
        mock_pyaudio.open.return_value = mock_stream
        mock_pyaudio_mdl.PyAudio.return_value = mock_pyaudio

        mock_stream.read.return_value = (
            b"\x04\x00\x08\x00\t\x00\x14\x00\x06\x00\xff\xff\xf5"
            b"\xff\xfc\xff\xf7\xff\xf8\xff\xf2\xff\x05\x00\x00\x00"
        )

        # act
        factory = PcFactory({})
        emitter = factory.create_emitter()
        receiver = factory.create_receiver()
        processor = factory.create_processor()

        emitter.check()
        receiver.check()

        emitter.emit_beep()
        sample = receiver.record_signal()
        result = processor.process(sample)


if __name__ == '__main__':
    unittest.main()
