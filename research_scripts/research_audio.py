
import math
import random
import threading
import time

import pyaudio


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 1

BYTES_PER_FRAME = 2
SOUND_FILENAME = "sound.dat"


# =============
# == HELPERS ==
# =============

def int_to_bytes(i):
    return i.to_bytes(BYTES_PER_FRAME, byteorder='little', signed=True)


def list_to_bytes(integers):
    return b''.join([int_to_bytes(i) for i in integers])


def volume_to_value(max_volume):
    if not 0. <= max_volume <= 1.:
        raise ValueError("max_volume is in range 0-1")
    max_value = int(max_volume * 2 ** (BYTES_PER_FRAME * 8) / 2)
    return max_value


def random_chunk(max_volume=0.):
    max_value = volume_to_value(max_volume)
    data = [random.randint(-max_value, max_value-1) for _ in range(CHUNK)]
    chunk = list_to_bytes(data)
    return chunk


def sine_wave(duration_ms, frequency, volume):
    amplitude = volume_to_value(volume)
    n_frames = int(duration_ms / 1000 * RATE)
    data = [
        int(amplitude * math.sin(2 * math.pi * frequency * i / RATE))
        for i in range(n_frames)
    ]
    chunks = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
    chunks = [list_to_bytes(c) for c in chunks]
    return chunks


def wavelet(duration_ms, frequency, volume):
    amplitude = volume_to_value(volume)
    duration_frames = duration_ms / 1000 * RATE
    n_frames = int(40 * duration_frames)
    gauss_outline_param = duration_frames / 2

    f_gauss = lambda i: math.exp(-(i/gauss_outline_param)**2)
    print(duration_ms, frequency, volume)
    f_sine = lambda i: math.sin(2 * math.pi * frequency * i / RATE)
    data = [
        int(amplitude * f_gauss(i) * f_sine(i))
        for i in range(-n_frames // 2, n_frames // 2)
    ]
    chunks = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
    chunks = [list_to_bytes(c) for c in chunks]
    save_recording(chunks, filename="original.dat")
    return chunks


def save_recording(chunks, filename=SOUND_FILENAME):
    byte_data = b"".join(chunks)
    with open(filename, 'wb') as f:
        f.write(byte_data)


def print_time(prefix, now):
    clock_time = time.strftime("%H:%M:%S", time.localtime(now))
    microseconds = f".{int(now * 1000000) % 1000000:06d}"
    print(prefix + clock_time + microseconds, flush=True)


# ======================
# == BUSINESS OBJECTS ==
# ======================

def emit_beep(p, chunks=None):
    # set stream
    now1 = time.time()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        output=True
    )
    time.sleep(0.11)
    now2 = time.time()
    print_time("pre play=  ", now1)
    print_time("post play= ", now2)

    # prepare data
    if chunks is None:
        chunks = wavelet(5.5, 3310, 1)
        print(len(chunks))
        '''chunks = [random_chunk(0.1) for i in range(200)]
        chunks = sine_wave(1, 6500, 1)'''

    # play sound
    print("Playing sound...")
    for data in chunks:
        stream.write(data)
    print("Playing ended")

    # destroy stream
    stream.stop_stream()
    stream.close()


def record_response(p):
    # set stream
    time.sleep(0.0)
    now3 = time.time()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    now4 = time.time()
    print_time("pre rec=   ", now3)
    print_time("post rec=  ", now4)


    # record
    print("Recording started...")
    chunks = [stream.read(CHUNK)
              for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS))]
    print("Recording stopped.")

    # destroy stream
    stream.stop_stream()
    stream.close()

    # return data
    return chunks


# =============
# == SCRIPTS ==
# =============

def main():
    p = pyaudio.PyAudio()

    t = threading.Thread(target=emit_beep, args=(p,))
    t.start()
    response = record_response(p)
    t.join()
    save_recording(response)
    time.sleep(1)
    emit_beep(p, response)

    p.terminate()


def test():
    data = 90*[1]
    chunks = [data[i:i + 20] for i in range(0, len(data), 20)]
    print(chunks)

    i = -32767
    print(i)
    print(int_to_bytes(i))
    print(list_to_bytes(20*[i]))

    random_chunk(0.1)

    p = pyaudio.PyAudio()
    sine = sine_wave(300, 600, 0.02)
    emit_beep(p, sine)
    time.sleep(1)
    sine = sine_wave(2, 2500, 1.0)
    emit_beep(p, sine)
    time.sleep(1)
    sine = sine_wave(300, 600, 0.42)
    emit_beep(p, sine)
    p.terminate()

    return


if __name__ == "__main__":
    #test()
    main()
