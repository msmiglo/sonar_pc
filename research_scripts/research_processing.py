
from matplotlib import colors
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter
from scipy.signal import find_peaks

from research_audio import BYTES_PER_FRAME, RATE, SOUND_FILENAME


RECORDING_FILENAME = "sound_samples/1200Hz_4ms.dat"
#RECORDING_FILENAME = "sound_samples/3kHz_05ms.dat"
#RECORDING_FILENAME = "sound_samples/5kHz_2ms.dat"
#RECORDING_FILENAME = "sound.dat"

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

    plt.colorbar(img, label='Amplitude')
    plt.ylabel('Frequency [Hz]')
    if y_annotations is not None:
        annotation_sparsity = len(y_annotations) // 20
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


def find_main_peak(matrix):
    # Find local maxima by comparing signal to its neighbors
    freq_window, time_window = 5, 30
    neighborhood = (freq_window, time_window)
    maximum_matrix = maximum_filter(matrix, size=neighborhood)
    local_max = (maximum_matrix == matrix)
    
    # Isolate the global maximum from the set of local maxima
    max_val = np.max(matrix)
    peak_mask = local_max & (matrix == max_val)
    # Get coordinates (row=frequency, col=sample)
    coords = np.argwhere(peak_mask)
    freq, time = coords[0]
    print("freq, time:", freq, time)
    return freq, time


def find_secondary_peaks(collapsed_signal, min_h, max_h, gap=30):
    """
    Finds peaks within a specific height range in a 1D signal.
    """
    # height is a tuple (min, max)
    peaks, props = find_peaks(
        collapsed_signal, 
        height=(min_h, max_h), 
        distance=gap,
        prominence=min_h
    )
    return list(zip(peaks, props['prominences']))


def process(samples):
    # wavelet transform
    plot(samples)
    frequencies = np.geomspace(700, 7000, 500)
    cwt_matrix = signal.cwt(
        samples, my_wavelet, frequencies)
    cwt_matrix = np.abs(cwt_matrix)
    plot_2d(cwt_matrix, y_annotations=frequencies)

    # find main pulse
    freq_index, offset = find_main_peak(cwt_matrix)
    freq = frequencies[freq_index]
    print("main freq = ", freq, "; freq_index = ", freq_index)
    freq_window_span = max(3, len(cwt_matrix) // 60)
    freq_low = freq_index - freq_window_span
    freq_high = freq_index + freq_window_span

    # cut out stripe around main freq
    cwt_stripe = cwt_matrix[freq_low:freq_high, :]
    plot_2d(cwt_stripe)

    # get background noise level
    noise = np.median(cwt_stripe)
    print("noise:", noise)

    # squeeze signal along freq axis
    signal_1d = np.sum(cwt_stripe, axis=0)
    plot(signal_1d)

    # finding peaks
    peaks = find_secondary_peaks(
        signal_1d, min_h=2*noise, max_h=np.amax(signal_1d)/2)
    peaks = peaks
    print(peaks)  # timings, heights

    # filter most relevant peaks
    peaks = list(filter(lambda pair: pair[0] > offset, peaks))
    if len(peaks) > 5:
        peaks = sorted(peaks, key=lambda pair: pair[1], reverse=True)
        peaks = list(peaks)[:5]
    print(peaks)

    # calculate distances from delays to main pulse
    new_peaks = []
    peaks = list(sorted(peaks, key=lambda pair: pair[0]))
    for timing, prominency in peaks:
        intensity = prominency / noise
        delay = (timing - offset) / RATE
        distance = delay * SOUND_SPEED / 2.
        new_peaks.append({"distance": distance, "intensity": intensity})

    # make results
    results = {
        "main_frequency": freq,
        "main_pulse_amplitude": np.amax(signal_1d),
        "main_signal_offset": offset,
        "noise_background": noise,
        "distances": new_peaks
    }
    return results


def format_results(results):
    rows = []
    for peak in results["distances"]:
        distance = peak["distance"]
        intensity = peak["intensity"]
        row = f"{distance:.2f} m\t(intensity {intensity:.2f})"
        if intensity < 200:
            row = f"[{row}] - not reliable"
        row = "\t" + row
        rows.append(row)
    rows = "\n".join(rows)

    txt = f"""
distance measured:
{rows}

main pulse signal-to-noise ratio: {
    int(results["main_pulse_amplitude"] / results["noise_background"])}
    """
    print(txt)


#############
## SCRIPTS ##
#############


def main():
    samples = load_recording(RECORDING_FILENAME)
    frequencies = np.geomspace(700, 7000, 500) 
    results = process(samples)
    format_results(results)


def test():
    pass
    #plot(np.real(my_wavelet(5000, 300)))


if __name__ == "__main__":
    test()
    main()
