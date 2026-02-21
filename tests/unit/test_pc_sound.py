
import unittest
from unittest.mock import call, MagicMock, patch

import numpy as np

from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample)
from modules.concrete.pc_sound import (
    PcEmitter, PcFactory, PcProcessor, PcReceiver, PcSample, _Series, _Stripe)
from modules.concrete.pc_sound import (
    ProcessorEmptyDataError,
    ProcessorNoInputError,
    ProcessorNoisyDataError,
    ProcessorNoPeaksDetectedError,
    ProcessorWrongFrequencyError
)
from modules.core import Result


class TestPcSample(unittest.TestCase):
    """
    - test volume to max
    - test max volume
    - test int from bytes
    - test int to bytes
    - test list to bytes
    - test call init without key
    - test base class
    - test from empty
    - test init
    - test len
    - test from_... wrong type
    - test from values
    - test from signal
    - test from data
    - test from chunks
    - test to values
    - test to signal
    - test to data
    - test to chunks
    """
    def setUp(self):
        self.sample = PcSample.__new__(PcSample)
        self.data_1 = b"\t\nE\x01\xef\xdd"
        self.signal_1 = [2569, 325, -8721]
        self.values_1 = [2569 / 32768, 325 / 32768, -8721 / 32768]

    # static methods

    def test_volume_to_max(self):
        result = self.sample._volume_to_int(0.1)
        self.assertEqual(result, 3276)

    def test_max_volume(self):
        result = self.sample._max_volume
        self.assertEqual(result, 32768)

    def test_int_from_bytes(self):
        input_ = b"7\xae"
        expected = -20937
        result = self.sample._int_from_bytes(input_)
        self.assertEqual(result, expected)

    def test_int_to_bytes(self):
        input_ = 9874
        input_2 = 0
        expected = b"\x92&"
        expected2 = b"\x00\x00"
        result = self.sample._int_to_bytes(input_)
        result2 = self.sample._int_to_bytes(input_2)
        self.assertEqual(result, expected)
        self.assertEqual(result2, expected2)

    def test_list_to_bytes(self):
        for input_, expected in [
                (self.signal_1, self.data_1), ([], b"")]:
            result = self.sample._list_to_bytes(input_)
            self.assertEqual(result, expected)

    # constructor

    def test_call_init_without_key(self):
        with self.assertRaises(AttributeError):
            PcSample(np.array([1., 2., 3.]))
        with self.assertRaises(TypeError):
            PcSample([1., 2., 3.], key=PcSample._PcSample__KEY)

    def test_base_class(self):
        self.assertTrue(issubclass(PcSample, AbstractSample))

    def test_from_empty(self):
        sample = PcSample(np.array([]), key=PcSample._PcSample__KEY)
        self.assertListEqual(list(sample._PcSample__values_array), [])

    def test_init(self):
        sample = PcSample(np.array(self.values_1),
                          key=PcSample._PcSample__KEY)
        self.assertListEqual(list(sample._PcSample__values_array),
                             self.values_1)

    # class methods

    def test_from_wrong_type(self):
        for arg, method in [
            (self.data_1, PcSample.from_values),
            (self.data_1, PcSample.from_signal),
            (str(self.data_1), PcSample.from_data),
            (self.signal_1, PcSample.from_chunks)
        ]:
            with self.assertRaises((TypeError, ValueError)):
                method(arg)

    def test_from_values(self):
        sample = PcSample.from_values(np.array(self.values_1))
        self.assertListEqual(
            list(sample._PcSample__values_array), self.values_1)

    def test_from_signal(self):
        sample = PcSample.from_signal(np.array(self.signal_1))
        self.assertListEqual(
            list(sample._PcSample__values_array), self.values_1)

    def test_from_data(self):
        sample = PcSample.from_data(self.data_1)
        self.assertListEqual(
            list(sample._PcSample__values_array), self.values_1)

    def test_from_chunks(self):
        sample = PcSample.from_chunks(
            [np.array(self.data_1), np.array(self.data_1),
             np.array(self.data_1)])
        self.assertListEqual(
            list(sample._PcSample__values_array), 3*self.values_1)

    # public methods

    def test_len(self):
        sample = PcSample.from_chunks(
            [np.array(self.data_1), np.array(self.data_1),
             np.array(self.data_1)])
        self.assertEqual(len(sample), 9)

    def test_to_values(self):
        sample = PcSample.from_signal(self.signal_1)
        result = list(sample.to_values())
        self.assertListEqual(result, self.values_1)

    def test_to_signal(self):
        sample = PcSample.from_values(self.values_1)
        result = list(sample.to_signal())
        self.assertListEqual(result, self.signal_1)

    def test_to_data(self):
        sample = PcSample.from_signal(self.signal_1)
        result = sample.to_data()
        self.assertEqual(result, self.data_1)

    def test_to_chunks(self):
        sample = PcSample.from_signal(2 * self.signal_1)
        result = sample.to_chunks()
        self.assertListEqual(result, [self.data_1 + self.data_1])

    @patch('modules.concrete.pc_sound.CHUNK', 5)
    def test_split_chunks(self):
        sample = PcSample.from_signal(4 * self.signal_1)
        result = sample.to_chunks()
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[0]), 2*5)
        self.assertEqual(len(result[1]), 2*5)
        self.assertEqual(len(result[2]), 2*2)

        sample2 = PcSample.from_signal(10 * self.signal_1)
        result2 = sample2.to_chunks()
        self.assertEqual(len(result2), 6)
        for res in result2:
            self.assertEqual(len(res), 2*5)


class TestPcFactory(unittest.TestCase):
    """
    - test creation
    - test destructor
    - test create objects
    - test check
    """
    def setUp(self):
        self.mock_driver = MagicMock()
        self.mock_factory = MagicMock(spec=PcFactory)
        self.mock_factory.pa = self.mock_driver

    @patch("modules.concrete.pc_sound.pyaudio.PyAudio")
    def test_creation(self, mock_audio):
        mock_audio.return_value = self.mock_driver
        factory = PcFactory({})
        self.assertTrue(isinstance(factory, AbstractFactory))
        self.assertIs(factory.pa, self.mock_driver)
        mock_audio.assert_called_once()

    @patch("modules.concrete.pc_sound.pyaudio.PyAudio")
    def test_destructor(self, mock_audio):
        mock_audio.return_value = self.mock_driver
        factory = PcFactory({})
        self.mock_driver.terminate.assert_not_called()
        del factory
        self.mock_driver.terminate.assert_called_once()

    @patch("modules.concrete.pc_sound.PcEmitter")
    def test_create_emitter(self, mock_emitter_class):
        PcFactory.create_emitter(self.mock_factory)
        mock_emitter_class.assert_called_once_with(
            {"pyaudio": self.mock_driver})

    @patch("modules.concrete.pc_sound.PcReceiver")
    def test_create_receiver(self, mock_receiver_class):
        PcFactory.create_receiver(self.mock_factory)
        mock_receiver_class.assert_called_once_with(
            {"pyaudio": self.mock_driver})

    @patch("modules.concrete.pc_sound.PcProcessor")
    def test_create_processor(self, mock_processor_class):
        PcFactory.create_processor(self.mock_factory)
        mock_processor_class.assert_called_once_with({})

    def test_check(self):
        with self.assertRaises(NotImplementedError):
            PcFactory.check(self.mock_factory)


class TestPcEmitter(unittest.TestCase):
    """
    - test init
    - test check
    - test make beep
    - test emit beep
    """
    def setUp(self):
        self.mock_pa = MagicMock()
        self.config = {"pyaudio": self.mock_pa}
        self.emitter = PcEmitter(self.config)

        self.mock_stream = MagicMock()
        self.mock_pa.open.return_value = self.mock_stream

    def test_init(self):
        self.assertEqual(self.emitter.config, self.config)
        self.assertEqual(self.emitter.pa, self.mock_pa)
        self.assertIsInstance(self.emitter, AbstractEmitter)

    def test_check(self):
        self.emitter.check()
        self.mock_pa.get_default_output_device_info.assert_called_once()
        self.mock_pa.open.assert_called_once()
        self.mock_stream.write.assert_called_with(b"")
        self.mock_stream.stop_stream.assert_called_once()
        self.mock_stream.close.assert_called_once()

    @patch('modules.concrete.pc_sound.PLAYING_DURATION_SECONDS', 0.001)
    @patch('modules.concrete.pc_sound.PcSample')
    def test_make_beep(self, mock_sample_class):
        # arrange
        mock_sample = MagicMock()
        mock_sample_class.from_values.return_value = mock_sample

        # act
        sample = self.emitter._make_beep_sample()

        # assert
        args, kwargs = mock_sample_class.from_values.call_args
        values = args[0]

        self.assertIsInstance(values, np.ndarray)
        self.assertEqual(len(values), 44)
        self.assertLessEqual(np.amax(np.abs(values)), 1.0)
        self.assertAlmostEqual(values[1], -values[-1])

    def test_emit_beep(self):
        # arrange
        mock_emitter = MagicMock(spec=PcEmitter)
        mock_emitter.pa = self.mock_pa
        mock_sample = MagicMock()
        mock_emitter._make_beep_sample.return_value = mock_sample
        fake_data = b"\x00\x01"
        expected_calls = 5 * [fake_data]
        mock_sample.to_chunks.return_value = expected_calls

        # act
        PcEmitter.emit_beep(mock_emitter)

        # assert
        self.mock_stream.write.assert_has_calls(map(call, expected_calls))
        self.mock_stream.stop_stream.assert_called_once_with()
        self.mock_stream.close.assert_called_once_with()


class TestPcReceiver(unittest.TestCase):
    """
    - test init
    - test check
    - test n_chunks
    - test stream called
    """
    def setUp(self):
        self.mock_pa = MagicMock()
        self.config = {"pyaudio": self.mock_pa}
        self.receiver = PcReceiver(self.config)

        self.mock_stream = MagicMock()
        self.mock_pa.open.return_value = self.mock_stream
        self.mock_chunk = MagicMock()

    def test_init(self):
        self.assertEqual(self.receiver.config, self.config)
        self.assertEqual(self.receiver.pa, self.mock_pa)
        self.assertIsInstance(self.receiver, AbstractReceiver)

    def test_check(self):
        self.receiver.check()
        self.mock_pa.get_default_input_device_info.assert_called_once()
        self.mock_pa.open.assert_called_once()
        self.mock_stream.read.assert_called_with(0)
        self.mock_stream.stop_stream.assert_called_once()
        self.mock_stream.close.assert_called_once()

    @patch('modules.concrete.pc_sound.CHUNK', 100)
    @patch('modules.concrete.pc_sound.PcSample')
    def test_n_chunks(self, mock_sample_class):
        mock_sample = MagicMock()
        mock_sample_class.from_chunks.return_value = mock_sample
        fake_data = b"\x00\x01"
        self.mock_stream.read.return_value = fake_data

        result = self.receiver.record_signal()

        n_chunks = self.mock_stream.read.call_count
        mock_sample_class.from_chunks.assert_called_once_with(
            n_chunks * [fake_data])
        self.assertIs(result, mock_sample)

    @patch('modules.concrete.pc_sound.CHUNK', 10)
    @patch('modules.concrete.pc_sound.PcSample')
    def test_stream_called(self, mock_sample_class):
        self.receiver.record_signal()
        self.mock_pa.open.assert_called_once()
        self.mock_stream.stop_stream.assert_called_once_with()
        self.mock_stream.close.assert_called_once_with()


class TestStripe(unittest.TestCase):
    """
    - test from sample
    - test wavelet
    - test get offset empty data
    - test get offset
    - test squeeze
    """
    def test_init_wrong_type(self):
        with self.assertRaises(TypeError):
            _Stripe.from_sample(np.linspace(2, 10))

    @patch('modules.concrete.pc_sound.STRIPE_N_FREQS', 33)
    def test_from_sample(self):
        # arrange
        mock_sample = MagicMock(spec=PcSample)
        mock_sample.to_values.return_value = np.zeros(100)
        # act
        stripe = _Stripe.from_sample(mock_sample)
        # assert
        mock_sample.to_values.assert_called_once_with()
        self.assertIsInstance(stripe._data, np.ndarray)
        self.assertIsInstance(stripe._frequencies, np.ndarray)
        self.assertTrue(np.all(stripe._data == 0))
        self.assertEqual(len(stripe._frequencies), 33)

    def test_wavelet(self):
        f = 1000
        for n in [1, 100, 101]:
            result = _Stripe._my_wavelet(n, f)
            self.assertEqual(len(result), n)
            self.assertIsInstance(result[0], (complex, np.complex128))
            self.assertAlmostEqual(result[n//2], 1 + 0j)

    def test_get_offset_empty(self):
        stripe = _Stripe()
        stripe._data = np.array([])
        with self.assertRaises(RuntimeError):
            stripe.get_offset()

    def test_get_offset(self):
        data = np.zeros((40, 100))
        data[20, 50] = 10.0
        stripe = _Stripe()
        stripe._data = data
        stripe._frequencies = np.arange(40) * 3

        freq, offset = stripe.get_offset()

        self.assertEqual(offset, 50)
        self.assertEqual(freq, 60)

    @patch('modules.concrete.pc_sound._Series')
    def test_squeeze(self, mock_series_cls):
        # arrange
        mock_series = MagicMock(spec=_Series)
        mock_series_cls.return_value = mock_series
        mock_stripe = MagicMock(spec=_Stripe)

        for input_, expected in [
            (np.array([[1, 2], [3, 4], [5, 6]]) , np.array([9, 12])),
            (np.array([]), np.array([]))
        ]:
            mock_stripe._data = input_
            # act
            result = _Stripe.squeeze(mock_stripe)
            # assert
            self.assertIs(result, mock_series)
            args, kwargs = mock_series_cls.call_args
            a = args[0]
            self.assertTrue(np.all(a == expected))


class TestSeries(unittest.TestCase):
    """
    - test init wrong data
    - test init
    - test get nps
    - test get peaks
    - test get peaks
    - test get noise
    - test get pulse max
    """
    def test_init_type_error(self):
        with self.assertRaises(TypeError):
            _Series([1, 2, 3])

    def test_init_success(self):
        data = np.array([1.0, 2.0])
        series = _Series(data)
        np.testing.assert_array_equal(series._series, data)

    def test_get_nps_metadata_logic(self):
        mock_self = MagicMock()
        mock_self._noise = 2.0
        mock_self._pulse_max = 10.0

        noise, pulse_max, snr = _Series.get_nps_metadata(self=mock_self)

        self.assertEqual(noise, 2.0)
        self.assertEqual(pulse_max, 10.0)
        self.assertEqual(snr, 5.0)

    @patch('modules.concrete.pc_sound.find_peaks')
    def test_get_peaks_empty(self, mock_find_peaks):
        # arrange
        mock_series = MagicMock()
        mock_series._noise = 2.0
        mock_series._pulse_max = 10.0
        mock_find_peaks.return_value = (
            np.array([]), {"prominences": np.array([])})
        # act
        peaks = _Series.get_peaks(mock_series)
        # assert
        self.assertListEqual(peaks, [])

    @patch('modules.concrete.pc_sound.SIGNAL_WIDTH_SECONDS', 1)
    @patch('modules.concrete.pc_sound.RATE', 100)
    @patch('modules.concrete.pc_sound.find_peaks')
    def test_get_peaks(self, mock_find_peaks):
        # arrange
        mock_series = MagicMock()
        mock_series._noise = 2.0
        mock_series._pulse_max = 10.0
        mock_find_peaks.return_value = (np.array([5]),
                                        {"prominences": np.array([10.0])})
        # act
        peaks = _Series.get_peaks(mock_series)
        # assert
        mock_find_peaks.assert_called_once_with(
            mock_series._series, height=(8., 2.5), distance=101, prominence=4)
        self.assertListEqual(peaks, [(5, 10)])

    def test_get_noise(self):
        mock_series = MagicMock()
        mock_series._series = np.array([1, 5, 10, 2])
        res = _Series._noise.fget(mock_series)
        self.assertEqual(res, 3.5)

    def test_get_pulse_max(self):
        mock_series = MagicMock()
        mock_series._series = np.array([-10, 100, 20])
        res = _Series._pulse_max.fget(mock_series)
        self.assertEqual(res, 100)


class TestPcProcessor(unittest.TestCase):
    """
    - test init and base
    - test sample empty error
    - test sample flat error
    - test sample wrong freq
    - test validate sample
    - test process low snr
    - test process no peaks
    - test process
    """
    def setUp(self):
        self.mock_proc = MagicMock(spec=PcProcessor)

    def test_base_class(self):
        with self.assertRaises(TypeError):
            PcProcessor()
        proc = PcProcessor({})
        self.assertIsInstance(proc, AbstractProcessor)

    def test_validate_sample_empty_error(self):
        mock_sample = MagicMock()
        mock_sample.__len__.return_value = 0
        with self.assertRaises(ProcessorNoInputError):
            PcProcessor._validate_sample(self.mock_proc, mock_sample)

    def test_validate_sample_flat_signal_error(self):
        mock_sample = MagicMock()
        mock_sample.__len__.return_value = 10
        mock_sample.to_values.return_value = 0.01 * np.ones(10)

        with self.assertRaises(ProcessorEmptyDataError):
            PcProcessor._validate_sample(self.mock_proc, mock_sample)

    @patch('modules.concrete.pc_sound.np.fft.fftfreq')
    def test_validate_sample_wrong_freq_error(self, mock_fft_freq):
        mock_sample = MagicMock()
        mock_sample.__len__.return_value = 4
        mock_sample.to_values.return_value = np.array([0, 1, 0, -1])
        mock_fft_freq.return_value = np.array([0, 5, 10, 15])

        with self.assertRaises(ProcessorWrongFrequencyError) as cm:
            PcProcessor._validate_sample(self.mock_proc, mock_sample)
        self.assertIn("5 Hz", str(cm.exception))

    @patch('modules.concrete.pc_sound.CARRIER_FREQUENCY', 121)
    @patch('modules.concrete.pc_sound.RATE', 1000)
    def test_validate_sample_success(self):
        # arrange
        n = 50
        f = 121
        values = 0.08 * np.sin(2 * np.pi * f / 1000 * np.arange(n))
        mock_sample = MagicMock()
        mock_sample.__len__.return_value = n
        mock_sample.to_values.return_value = values

        # act
        f_max = PcProcessor._validate_sample(self.mock_proc, mock_sample)

        # assert
        self.assertAlmostEqual(f_max, 120)

    @patch('modules.concrete.pc_sound.Result')
    @patch('modules.concrete.pc_sound._Stripe')
    @patch('modules.concrete.pc_sound.SNR_THRESHOLD', 10.0)
    def test_process_low_snr_error(self, mock_stripe_cls, mock_result_cls):
        mock_sample = MagicMock()
        mock_stripe = MagicMock()
        mock_series = MagicMock()
        mock_result = MagicMock()

        self.mock_proc._validate_sample.return_value = 369.
        mock_result_cls.from_error.return_value = mock_result
        mock_stripe_cls.from_sample.return_value = mock_stripe

        mock_stripe.get_offset.return_value = (375., 123)
        mock_stripe.squeeze.return_value = mock_series
        mock_series.get_nps_metadata.return_value = (5.55, 5, 0.9)

        # act
        result = PcProcessor.process(self.mock_proc, sample=mock_sample)

        # assert
        self.assertIs(result, mock_result)

        kwargs = {
            "f_max": 369., "f_max_stripe": 375., "noise": 5.55, "snr": 0.9}
        mock_stripe_cls.from_sample.assert_called_once_with(mock_sample)
        error_arg, error_kwargs = mock_result_cls.from_error.call_args
        self.assertIsInstance(error_arg[0], ProcessorNoisyDataError)
        self.assertDictEqual(error_kwargs, kwargs)

        self.mock_proc._validate_sample.assert_called_once_with(mock_sample)
        mock_stripe.get_offset.assert_called_once_with()
        mock_stripe.squeeze.assert_called_once_with()
        mock_series.get_nps_metadata.assert_called_once_with()

    @patch('modules.concrete.pc_sound._Stripe')
    @patch('modules.concrete.pc_sound.Result')
    def test_process_no_peaks_error(self, mock_result_cls, mock_stripe_cls):
        mock_sample = MagicMock()
        mock_stripe = MagicMock()
        mock_series = MagicMock()
        mock_result = MagicMock()

        self.mock_proc._validate_sample.return_value = 369.
        self.mock_proc._filter_peaks.return_value = 'filtered_data'
        self.mock_proc._process_peaks.return_value = []

        mock_result_cls.from_error.return_value = mock_result
        mock_stripe_cls.from_sample.return_value = mock_stripe

        mock_stripe.get_offset.return_value = (375., 123)
        mock_stripe.squeeze.return_value = mock_series
        mock_series.get_nps_metadata.return_value = (0.146, 65, 445.21)
        mock_series.get_peaks.return_value = 'peaks_data'

        # act
        result = PcProcessor.process(self.mock_proc, sample=mock_sample)

        # assert
        self.assertIs(result, mock_result)

        kwargs = {
            "f_max": 369., "f_max_stripe": 375., "noise": 0.146, "snr": 445.21}
        mock_stripe_cls.from_sample.assert_called_once_with(mock_sample)
        error_arg, error_kwargs = mock_result_cls.from_error.call_args
        self.assertIsInstance(error_arg[0], ProcessorNoPeaksDetectedError)
        self.assertDictEqual(error_kwargs, kwargs)

        self.mock_proc._validate_sample.assert_called_once_with(mock_sample)
        self.mock_proc._filter_peaks.assert_called_once_with('peaks_data', 123)
        self.mock_proc._process_peaks.assert_called_once_with(
            'filtered_data', 123, 0.146)

        mock_stripe.get_offset.assert_called_once_with()
        mock_stripe.squeeze.assert_called_once_with()
        mock_series.get_nps_metadata.assert_called_once_with()
        mock_series.get_peaks.assert_called_once_with()

    @patch('modules.concrete.pc_sound._Stripe')
    @patch('modules.concrete.pc_sound.Result')
    @patch('modules.concrete.pc_sound.SNR_THRESHOLD', 10.0)
    def test_process(self, mock_result_cls, mock_stripe_cls):
        # arrange
        mock_sample = MagicMock()
        mock_stripe = MagicMock()
        mock_series = MagicMock()
        mock_result = MagicMock()

        self.mock_proc._validate_sample.return_value = 369.
        self.mock_proc._filter_peaks.return_value = 'filtered_data'
        self.mock_proc._process_peaks.return_value = 'processed_data'

        mock_result_cls.return_value = mock_result
        mock_stripe_cls.from_sample.return_value = mock_stripe

        mock_stripe.get_offset.return_value = (375., 123)
        mock_stripe.squeeze.return_value = mock_series
        mock_series.get_nps_metadata.return_value = (0.146, 65, 445.21)
        mock_series.get_peaks.return_value = 'peaks_data'

        # act
        result = PcProcessor.process(self.mock_proc, sample=mock_sample)

        # assert
        self.assertIs(result, mock_result)

        kwargs = {
            "f_max": 369., "f_max_stripe": 375., "noise": 0.146, "snr": 445.21}
        mock_stripe_cls.from_sample.assert_called_once_with(mock_sample)
        mock_result_cls.assert_called_once_with('processed_data', **kwargs)

        self.mock_proc._validate_sample.assert_called_once_with(mock_sample)
        self.mock_proc._filter_peaks.assert_called_once_with('peaks_data', 123)
        self.mock_proc._process_peaks.assert_called_once_with(
            'filtered_data', 123, 0.146)

        mock_stripe.get_offset.assert_called_once_with()
        mock_stripe.squeeze.assert_called_once_with()
        mock_series.get_nps_metadata.assert_called_once_with()
        mock_series.get_peaks.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
