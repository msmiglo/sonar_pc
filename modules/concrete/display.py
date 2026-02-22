
from modules.abstract.abstract_display import AbstractDisplay


TEMPLATE = \
"""=========================
Distance:
{peaks}

background noise: {noise:.02f}
signal-to-noise ratio: {snr:.01f}{error}

{metadata}"""
PEAK_TEMPLATE = "{distance:.02f} m\tintensity: {intensity:.02f}"


class TextDisplay(AbstractDisplay):
    def __init__(self, config: dict=None):
        if config is None:
            config = {}
        self.config = config

    @staticmethod
    def _format_peak(peak=None):
        if peak is None:
            peak = dict(distance=0, intensity=0, reliable=False)
        txt = PEAK_TEMPLATE.format(
            distance=peak["distance"], intensity=peak["intensity"])
        if peak["reliable"] is False:
            txt = f"[{txt}] - unreliable"
        txt = "\t" + txt
        return txt

    def print(self, result):
        # get data
        data_dict = result.to_dict()

        # peaks message
        if data_dict["peaks"]:
            peaks_txt = "\n".join(map(self._format_peak, data_dict["peaks"]))
        else:
            if data_dict["error"]:
                peaks_txt = self._format_peak()
            else:
                peaks_txt = "\t[no data]"

        # error message
        if data_dict["error"]:
            error_txt = "\n\n[ERROR] " + data_dict["error"]
        else:
            error_txt = ""

        # print
        txt = TEMPLATE.format(peaks=peaks_txt, noise=data_dict["noise"],
                              snr=data_dict["snr"], error=error_txt,
                              metadata=data_dict["metadata"])
        print(txt, flush=True)
