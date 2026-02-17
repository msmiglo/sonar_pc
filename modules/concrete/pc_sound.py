
import math
import time

import numpy as np
import pyaudio
from scipy import signal
from scipy.ndimage import maximum_filter
from scipy.signal import find_peaks

from modules.abstract.abstract_factory import (
    AbstractEmitter, AbstractFactory, AbstractProcessor,
    AbstractReceiver, AbstractSample
)
from modules.core import Result


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
BYTES_PER_FRAME = 2
SOUND_SPEED = 343.0  # [m/s]
WL_GAUSS_PARAM = 0.0004  # [-]  (bigger param - shorter contour)


class PcSample(AbstractSample):
    def __init__(self, data_bytes: bytes):
        self.signal = data_bytes


class PcEmitter(AbstractEmitter):
    def __init__(self, config):
        self.config = config
        self.pa = config["pyaudio"]

    @staticmethod
    def _int_to_bytes(i):
        return i.to_bytes(BYTES_PER_FRAME, byteorder='little', signed=True)

    @staticmethod
    def _list_to_bytes(integers):
        return b''.join([PcEmitter._int_to_bytes(i) for i in integers])

    @staticmethod
    def _volume_to_value(volume):
        if not 0. <= volume <= 1.:
            raise ValueError("max_volume is in range 0-1")
        value = int(volume * 2 ** (BYTES_PER_FRAME * 8) / 2)
        return value

    @staticmethod
    def _make_beep_data(duration_ms, frequency, volume):
        amplitude = PcEmitter._volume_to_value(volume)
        duration_frames = duration_ms / 1000 * RATE
        n_frames = int(40 * duration_frames)
        gauss_outline_param = duration_frames / 2

        f_gauss = lambda i: math.exp(-(i/gauss_outline_param)**2)
        f_sine = lambda i: math.sin(2 * math.pi * frequency * i / RATE)
        data = [
            int(amplitude * f_gauss(i) * f_sine(i))
            for i in range(-n_frames // 2, n_frames // 2)
        ]
        chunks = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
        chunks = [PcEmitter._list_to_bytes(c) for c in chunks]
        return chunks

    def check(self):
        self.pa.get_default_output_device_info()
        stream = self.pa.open(
            format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
        stream.write(b"")
        stream.stop_stream()
        stream.close()

    def emit_beep(self):
        duration_ms = 2.5
        frequency = 3310
        volume = 1.
        chunks = self._make_beep_data(duration_ms, frequency, volume)

        stream = self.pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True
        )
        time.sleep(0*0.012)
        for data in chunks:
            stream.write(data)
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
        seconds = self.config.get("record_seconds", 3*0.092)
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

        return PcSample(b"".join(chunks))


class PcProcessor(AbstractProcessor):
    def __init__(self, config):
        self.config = config

    @staticmethod
    def _bytes_to_integer(data):
        return int.from_bytes(data, byteorder="little", signed=True)

    @staticmethod
    def _my_wavelet(n, f):
        x = np.arange(-n//2, -n//2 + n)
        a = 2 * np.pi * f / RATE * x
        return np.exp(-WL_GAUSS_PARAM * a**2 + 1j * a)

    def process(self, sample: PcSample) -> Result:
        if not isinstance(sample.signal, bytes):
            raise TypeError("data sample should contain bytes")

        # convert bytes to integers
        byte_data = sample.signal
        fragments = [byte_data[i:i + BYTES_PER_FRAME]
                 for i in range(0, len(byte_data), BYTES_PER_FRAME)]
        integer_list = list(map(self._bytes_to_integer, fragments))

        # CWT analysis
        frequencies = np.geomspace(700, 7000, 500)
        cwt_matrix = np.abs(signal.cwt(
            integer_list, self._my_wavelet, frequencies))

        # peak detection
        neighborhood = (5, 30)
        max_matrix = maximum_filter(cwt_matrix, size=neighborhood)
        peak_mask = (max_matrix == cwt_matrix) & \
                    (cwt_matrix == np.amax(cwt_matrix))
        coords = np.argwhere(peak_mask)
        freq_idx, offset = coords[0]

        # noise and squeezing
        span = max(3, len(cwt_matrix) // 60)
        stripe = cwt_matrix[freq_idx - span : freq_idx + span, :]
        noise = np.median(stripe)
        signal_1d = np.sum(stripe, axis=0)
        snr = np.amax(signal_1d) / noise

        # distance calculation
        peaks, props = find_peaks(
            signal_1d, height=(2*noise, np.amax(signal_1d)/2),
            distance=30, prominence=2*noise)
        zipped_peaks = list(zip(peaks, props["prominences"]))

        if len(peaks) == 0:
            e = RuntimeError("no response peaks found.")
            return Result.from_error(
                peaks=peaks, noise=noise, snr=snr, error=e)

        valid_peaks = list(filter(lambda pair: pair[0] > offset, zipped_peaks))
        if len(valid_peaks) > 5:
            valid_peaks = sorted(valid_peaks,
                                 key=lambda pair: pair[1], reverse=True)
            valid_peaks = list(valid_peaks)[:5]

        if len(valid_peaks) == 0:
            e = RuntimeError("all peaks lie before the main pulse")
            return Result.from_error(
                peaks=valid_peaks, noise=noise, snr=snr, error=e)

        new_peaks = []
        for timing, prominency in valid_peaks:
            delay = (timing - offset) / RATE
            distance = delay * SOUND_SPEED / 2.
            intensity = prominency / noise
            new_peaks.append((distance, intensity))

        result = Result(
            peaks=new_peaks,
            noise=noise,
            snr=snr
        )
        return result


class PcFactory(AbstractFactory):
    def __init__(self, config):
        self.config = config
        self.pa = pyaudio.PyAudio()

    def __del__(self):
        self.pa.terminate()

    def create_emitter(self) -> PcEmitter:
        return PcEmitter(self.config.get("emitter", {"pyaudio": self.pa}))

    def create_receiver(self) -> PcReceiver:
        return PcReceiver(self.config.get("receiver", {"pyaudio": self.pa}))

    def create_processor(self) -> PcProcessor:
        return PcProcessor(self.config.get("processor", {}))

    def check(self):
        raise NotImplementedError("not used yet")
        p = pyaudio.PyAudio()
        p.terminate()
