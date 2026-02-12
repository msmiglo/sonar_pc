
from matplotlib import colors
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

from research_audio import BYTES_PER_FRAME, RATE, SOUND_FILENAME


#RECORDING_FILENAME = "sound_samples/1200Hz_4ms.dat"
RECORDING_FILENAME = "sound_samples/3kHz_05ms.dat"
#RECORDING_FILENAME = "sound_samples/5kHz_2ms.dat"
RECORDING_FILENAME = "sound.dat"

SOUND_SPEED = 343.  # [m/s]
WL_GAUSS_PARAM = 0.0004  # [-]  (the bigger, the shorter contour)


###############
## UTILITIES ##
###############


def bytes_to_integer(data):
    return int.from_bytes(data, byteorder='little', signed=True)


def load_recording(filename=SOUND_FILENAME):
    with open(filename, 'rb') as f:
        byte_data = f.read()
    fragments = [byte_data[i:i + BYTES_PER_FRAME]
                 for i in range(0, len(byte_data), BYTES_PER_FRAME)]
    samples = list(map(bytes_to_integer, fragments))
    return samples


def plot(list_of_ints):
    plt.figure(figsize=(12, 4), dpi=100)
    plt.plot(list_of_ints, linewidth=0.3, color='#1f77b4')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
    plt.title("Sonar Signal")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    plt.show()


def plot_2d(data_2d, y_annotations=None):
    limit = np.max(data_2d)

    #plt.figure(figsize=(10, 6))
    img = plt.imshow(
        data_2d,
        aspect='auto',
        interpolation='nearest',
        norm=colors.LogNorm(vmin=limit/100, vmax=limit)
        #vmin = 0.,
        #vmax = limit
    )

    annotation_sparsity = len(y_annotations) // 20   
    plt.colorbar(img, label='Amplitude')
    plt.ylabel('Frequency [Hz]')
    if y_annotations is not None:
        y_annotations = list(map(round, y_annotations))
        plt.yticks(
            list(range(len(y_annotations)))[::annotation_sparsity],
            y_annotations[::annotation_sparsity]
        )
    plt.xlabel('Time (Samples)')
    plt.show()


####################
## BUSINESS LOGIC ##
####################


def my_wavelet(n, f):
    """
    n - number of sample points
    f - frequency of carrier wave
    """
    x = np.arange(-n//2, -n//2 + n)
    a = 2 * np.pi * f / RATE * x
    y = np.exp(-WL_GAUSS_PARAM * a**2 + 1j * a)
    return y


def process(samples):
    # wavelet transform
    plot(samples)
    frequencies = np.geomspace(700, 7000, 500)
    cwt_matrix = signal.cwt(
        samples, my_wavelet, frequencies)
    plot_2d(np.abs(cwt_matrix), y_annotations=frequencies)

    # finding peaks
    offset = None
    freq = None
    peaks = []

    # finding background noise
    noise = None

    # make results
    results = {
        "main_frequency": freq,
        "main_signal_offset": offset,
        "noise_background": noise,
        "distances": peaks
    }
    return results


#############
## SCRIPTS ##
#############


def main():
    samples = load_recording(RECORDING_FILENAME)
    frequencies = np.geomspace(700, 7000, 500) 
    results = process(samples)
    print(results)


def test():
    pass
    #plot(np.real(my_wavelet(5000, 300)))


if __name__ == "__main__":
    test()
    main()
