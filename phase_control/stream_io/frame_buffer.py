# phase_control/stream_io/frame_buffer.py
from multiprocessing import Value
import threading
from typing import Optional

import numpy as np

from phase_control.domain.models import Spectrum

from .models import StreamFrame, StreamMeta


class FrameBuffer:
    """
    Thread-safe buffer that always stores only the latest frame.

    - update(frame): store a new frame (overwrites previous one)
    - get_latest(): return the most recent frame or None if nothing yet
    """

    def __init__(self, meta: StreamMeta) -> None:
        self._lock = threading.Lock()
        self._latest: Optional[StreamFrame] = None
        self.meta: StreamMeta = meta

    def update(self, frame: StreamFrame) -> None:
        """Store a new frame, overwriting any previous frame."""
        with self._lock:
            self._latest = frame

    def get_latest(self) -> Spectrum:
        """
        Return the most recent frame, or None if no frame has been stored yet.
        """
        if self._latest is None:
            raise ValueError("No frame detected.")
        with self._lock:
            return self._generate_Spectrogram(self._latest)

    def _generate_Spectrogram(self, frame: StreamFrame) -> Spectrum:
        if self.meta.wavelengths is not None:
            return Spectrum.from_raw_data(self.meta.wavelengths, frame.counts)
        else:
            raise ValueError("Wavelengths not readable.")
        
        