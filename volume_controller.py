"""
volume_controller.py
--------------------
Windows system volume control via pycaw.
Provides a clean interface: set_volume(0.0 – 1.0), get_volume(), mute/unmute.
"""

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import math


class VolumeController:
    def __init__(self):
        devices = AudioUtilities.GetSpeakers()
        # pycaw >= 20240210 wraps the device in AudioDevice; the COM IMMDevice lives at ._dev
        raw_device = devices._dev if hasattr(devices, "_dev") else devices
        interface = raw_device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self._volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Hardware dB range
        self._vol_range = self._volume.GetVolumeRange()   # (min_dB, max_dB, step)
        self.min_db = self._vol_range[0]
        self.max_db = self._vol_range[1]

    # ------------------------------------------------------------------
    def set_volume_scalar(self, scalar: float):
        """
        Set volume using a linear 0.0 – 1.0 scalar.
        Converts to dB internally for smoother perceptual scaling.
        """
        scalar = max(0.0, min(1.0, scalar))
        db = self.min_db + (self.max_db - self.min_db) * scalar
        self._volume.SetMasterVolumeLevel(db, None)

    def get_volume_scalar(self) -> float:
        """Return current volume as 0.0 – 1.0."""
        db = self._volume.GetMasterVolumeLevel()
        return (db - self.min_db) / (self.max_db - self.min_db)

    def get_volume_percent(self) -> int:
        return round(self.get_volume_scalar() * 100)

    def mute(self):
        self._volume.SetMute(1, None)

    def unmute(self):
        self._volume.SetMute(0, None)

    def toggle_mute(self):
        muted = self._volume.GetMute()
        self._volume.SetMute(not muted, None)
        return not muted

    def is_muted(self) -> bool:
        return bool(self._volume.GetMute())
