
import math
import time

import numpy as np
import pyaudio
from scipy import signal
from scipy.ndimage import gaussian_filter1d, maximum_filter
from scipy.signal import find_peaks

from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample
)
from modules.core import Result


CHUNK = 1024  # [frames]
RATE = 44100  # [frames / s]

CHANNELS = 1
BYTES_PER_FRAME = 2
FORMAT = pyaudio.paInt16

PLAY_DELAY_SECONDS = 19 / 1000  # [s]
PLAYING_DURATION_SECONDS = 100 / 1000  # [s]
RECORDING_MARGIN_SECONDS = 340 / 1000  # [s]
SIGNAL_WIDTH_SECONDS = 2.5 / 1000  # [s]
CARRIER_FREQUENCY = 3310  # [Hz]

WL_GAUSS_PARAM = 0.0004  # [-]  (bigger param - shorter contour)
SOUND_SPEED = 343.0  # [m/s]
EPSILON = 1e-6

FREQ_BLUR_POINTS = 6.0
FREQ_TOLERANCE = 0.07
STRIPE_N_FREQS = 20
SNR_THRESHOLD = 10


class _BaseProcessorError(RuntimeError): pass

class ProcessorEmptyDataError(_BaseProcessorError): pass
class ProcessorNoSoundError(_BaseProcessorError): pass
class ProcessorWrongFrequencyError(_BaseProcessorError): pass
class ProcessorNoisyDataError(_BaseProcessorError): pass
class ProcessorNoPeaksDetectedError(_BaseProcessorError): pass


class PcSample(AbstractSample):
    """
    Glossary:

    == SOUND-RELATED ==
    - sample: whole object containing wave record (1D recording
        of air movements in time), consisting of sample-points
    - sample-point: one pixel of sound; a.k.a. `frame`
    - sample data representations:
        * values: float values normalized to [-1., 1.]
        * signal: int values corresponding to max range
        * data: bytes data ready to be streamed
        * chunks: bytes data divided into packets (CHUNK length
            corresponds to number of sample-points NOT bytes)
    - stripe: a sound data in 2D domain: time and frequency, after
        conducting a wavelet transform or other operation, containing
        only data for predefined range of frequencies, so it it both
        reduntant and lossy
    - series: stripe squeezed along frequency axis (summed up), so
        it is a 1D data showing energy of sound wave in time domain

    == SERIES-RELATED TERMS ==
    - main pulse: the original signal emitted by emmiter and
        caught on the microphone, identified as the main peak in
        the series data
    - peak: secondary peak willingly associated with sound reflections
    - noise: median of the series values
    - snr: signal-to-noise ratio, corresponding to main pulse: its
        height divided by noise

    == PEAK-RELATED TERMS ==
    - time domain:
        * offset: index of sample-point where the main pulse is located
        * timing: index of sample-point of secondary peaks
        * delay: timing divided by RATE - which is time in seconds
        * distance: computed based on delay and SOUND_SPEED, in meters
    - amplitude domain:
        * height: amplitude of peaks identified in the series
        * prominence: height relatively to neighbouring "valleys"
        * intensity: prominence divided by noise
    """
    __KEY = object()

    def __init__(self, values, key=None):
        if not key is self.__KEY:
            raise AttributeError(
                "cannot call constructor directly, "
                "use one of the `from_...` method")
        if not isinstance(values, np.ndarray):
            raise TypeError("values should be `numpy.ndarray` of floats")
        self.__values_array = values

    def __len__(self):
        return len(self.__values_array)

    #############################

    @classmethod
    def from_values(cls, values):
        values = np.array(values).astype(float)
        return cls(values, key=cls.__KEY)

    @classmethod
    def from_signal(cls, signal):
        signal = np.array(signal)
        values = signal / cls._max_volume
        return cls.from_values(values)

    @classmethod
    def from_data(cls, data):
        fragments = [
            data[i:i + BYTES_PER_FRAME]
            for i in range(0, len(data), BYTES_PER_FRAME)
        ]
        signal = list(map(cls._int_from_bytes, fragments))
        return cls.from_signal(signal)

    @classmethod
    def from_chunks(cls, chunks):
        data = b"".join(chunks)
        return cls.from_data(data)

    #############################

    def to_values(self):
        return self.__values_array

    def to_signal(self):
        values = self.to_values()
        signal = values * self._max_volume
        return signal.astype(int)

    def to_data(self):
        signal = self.to_signal()
        data = self._list_to_bytes(signal)
        return data

    def to_chunks(self):
        signal = self.to_signal()
        fragments = [signal[i:i + CHUNK] for i in range(0, len(self), CHUNK)]
        chunks = list(map(self._list_to_bytes, fragments))
        return chunks

    #############################

    @staticmethod
    def _volume_to_int(volume):
        if not 0. <= volume <= 1.:
            raise ValueError("max_volume is in range 0-1")
        value = int(volume * 2 ** (BYTES_PER_FRAME * 8) / 2)
        return value

    @staticmethod
    def _int_from_bytes(frame):
        return int.from_bytes(frame, byteorder="little", signed=True)

    @staticmethod
    def _int_to_bytes(i):
        return int(i).to_bytes(
            BYTES_PER_FRAME, byteorder='little', signed=True)

    @staticmethod
    def _list_to_bytes(integers):
        return b''.join(map(PcSample._int_to_bytes, integers))


PcSample._max_volume = PcSample._volume_to_int(1)


class PcEmitter(AbstractEmitter):
    def __init__(self, config):
        self.config = config
        self.pa = config["pyaudio"]

    def check(self):
        self.pa.get_default_output_device_info()
        stream = self.pa.open(
            format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
        stream.write(b"")
        stream.stop_stream()
        stream.close()

    @staticmethod
    def _make_beep_sample():
        amplitude = 1.
        signal_half_width_points = SIGNAL_WIDTH_SECONDS / 2 * RATE
        f_gauss = lambda i: np.exp(-(i / signal_half_width_points) ** 2)
        f_sine = lambda i: np.sin(2 * np.pi * CARRIER_FREQUENCY * i / RATE)

        n_points = int(PLAYING_DURATION_SECONDS * RATE)
        points = np.arange(-n_points // 2, n_points // 2)

        values = amplitude * f_gauss(points) * f_sine(points)
        sample = PcSample.from_values(values)

        return sample

    def emit_beep(self):
        beep_sample = self._make_beep_sample()
        chunks = beep_sample.to_chunks()

        stream = self.pa.open(
            format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
        time.sleep(PLAY_DELAY_SECONDS)
        for chunk in chunks:
            stream.write(chunk)
        stream.stop_stream()
        stream.close()


class PcReceiver(AbstractReceiver):
    def __init__(self, config):
        self.config = config
        self.pa = config["pyaudio"]

    def check(self):
        self.pa.get_default_input_device_info()
        stream = self.pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                              input=True, frames_per_buffer=CHUNK)
        stream.read(0)
        stream.stop_stream()
        stream.close()

    def record_signal(self) -> PcSample:
        seconds = 2 * PLAY_DELAY_SECONDS + PLAYING_DURATION_SECONDS \
                  + RECORDING_MARGIN_SECONDS
        n_chunks = int(RATE / CHUNK * seconds) + 1

        stream = self.pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        chunks = [stream.read(CHUNK)
                  for _ in range(n_chunks)]
        stream.stop_stream()
        stream.close()

        return PcSample.from_chunks(chunks)


class _Stripe:
    @classmethod
    def from_sample(cls, sample):
        if not isinstance(sample, PcSample):
            raise TypeError("please provide a `PcSample` instance as input")

        freq_low = CARRIER_FREQUENCY * (1 - FREQ_TOLERANCE)
        freq_high = CARRIER_FREQUENCY * (1 + FREQ_TOLERANCE)
        frequencies = np.geomspace(freq_low, freq_high, STRIPE_N_FREQS)

        stripe = cls()
        stripe._data = np.abs(signal.cwt(
            sample.to_values(), cls._my_wavelet, frequencies))
        stripe._frequencies = frequencies
        return stripe

    @staticmethod
    def _my_wavelet(n, f):
        n_low = -(n // 2)
        x = np.arange(n_low, n_low + n)
        a = 2 * np.pi * f / RATE * x
        return np.exp(-WL_GAUSS_PARAM * a**2 + 1j * a)

    def get_offset(self):
        freq_window = STRIPE_N_FREQS // 4
        timing_window = int(SIGNAL_WIDTH_SECONDS * RATE + 1)
        neighborhood = (freq_window, timing_window)
        stripe_max = maximum_filter(self._data, size=neighborhood)
        peak_mask = (stripe_max == self._data) & \
                    (self._data == np.amax(self._data))
        coords = np.argwhere(peak_mask)
        freq_idx, offset = coords[0]
        freq = self._frequencies[freq_idx]
        return freq, offset

    def squeeze(self) -> "_Series":
        series = np.sum(self._data, axis=0)
        return _Series(series)


class _Series:
    def __init__(self, series):
        if not isinstance(series, np.ndarray):
            raise TypeError('please provide numpy array as input')
        self._series = series

    def get_nps_metadata(self):
        noise = self._noise
        pulse_max = self._pulse_max
        snr = pulse_max / noise
        return noise, pulse_max, snr

    def get_peaks(self):
        noise = self._noise
        pulse_max = self._pulse_max
        height_span = (4 * noise, pulse_max / 4)
        distance = int(SIGNAL_WIDTH_SECONDS * RATE + 1)
        prominence = 2 * noise

        timings, properties = find_peaks(
            self._series, height=height_span,
            distance=distance, prominence=prominence
        )
        peaks = list(zip(timings, properties["prominences"]))
        return peaks

    @property
    def _noise(self):
        return np.median(self._series)

    @property
    def _pulse_max(self):
        return np.amax(self._series)


class PcProcessor(AbstractProcessor):
    def __init__(self, config):
        self.config = config

    def _validate_sample(self, sample):
        n = len(sample)
        if len(sample) == 0:
            raise ProcessorEmptyDataError("sample is empty")

        values = sample.to_values()
        if np.amax(values) - np.amin(values) < EPSILON:
            raise ProcessorNoSoundError(
                "signal is flat - no sound found")

        amps = np.fft.fft(values)
        freqs = np.fft.fftfreq(n, d=1/RATE)
        half_n = n // 2
        freqs = freqs[:half_n]
        amps = amps[:half_n]
        amps = np.abs(amps)
        amps = gaussian_filter1d(amps, sigma=FREQ_BLUR_POINTS, mode='constant')

        i_max = amps.argmax()
        f_max = freqs[i_max]
        f_low = CARRIER_FREQUENCY * (1 - FREQ_TOLERANCE)
        f_high = CARRIER_FREQUENCY * (1 + FREQ_TOLERANCE)

        if not f_low < f_max < f_high:
            raise ProcessorWrongFrequencyError(
                f"measured frequency of carrier-wave: {f_max:.0f} Hz "
                f"does not match the expected one: {CARRIER_FREQUENCY:.0f} Hz")

        return f_max

    def _filter_peaks(self, raw_peaks, offset):
        valid_peaks = list(filter(lambda pair: pair[0] > offset, raw_peaks))
        if len(valid_peaks) > 5:
            valid_peaks = sorted(
                valid_peaks, key=lambda pair: pair[1], reverse=True)
            valid_peaks = list(valid_peaks)[:5]
        return valid_peaks

    def _process_peaks(self, valid_peaks, offset, noise):
        peaks = []
        for timing, prominency in valid_peaks:
            delay = (timing - offset) / RATE
            distance = delay * SOUND_SPEED / 2.
            intensity = prominency / noise
            peaks.append((distance, intensity))

        return peaks

    def process(self, sample: PcSample) -> Result:
        kwargs = {}

        try:
            # check sample
            f_max = self._validate_sample(sample)
            kwargs["f_max"] = f_max

            # wavelet transform
            stripe = _Stripe.from_sample(sample)
            f_max_stripe, offset = stripe.get_offset()
            series = stripe.squeeze()
            kwargs["f_max_stripe"] = f_max_stripe

            # get metadata
            noise, pulse_max, snr = series.get_nps_metadata()
            kwargs["noise"] = noise
            kwargs["snr"] = snr

            if snr <= SNR_THRESHOLD:
                raise ProcessorNoisyDataError(
                    f"signal-to-noise ratio too small: {snr}")

            # get peaks
            raw_peaks = series.get_peaks()
            valid_peaks = self._filter_peaks(raw_peaks, offset)
            peaks = self._process_peaks(valid_peaks, offset, noise)

            if len(peaks) == 0:
                raise ProcessorNoPeaksDetectedError("no valid peaks found")

            # combine data to result
            result = Result(peaks, **kwargs)

        except _BaseProcessorError as e:
            # report error
            result = Result.from_error(e, **kwargs)

        return result


class PcFactory(AbstractFactory):
    def __init__(self, config):
        self.config = config
        self.pa = pyaudio.PyAudio()

    def __del__(self):
        self.pa.terminate()

    def create_emitter(self) -> PcEmitter:
        return PcEmitter({"pyaudio": self.pa})

    def create_receiver(self) -> PcReceiver:
        return PcReceiver({"pyaudio": self.pa})

    def create_processor(self) -> PcProcessor:
        return PcProcessor({})

    def check(self):
        raise NotImplementedError("not used yet")
        pa = pyaudio.PyAudio()
        pa.terminate()
