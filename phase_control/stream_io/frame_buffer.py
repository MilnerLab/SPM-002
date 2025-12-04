# phase_control/stream_io/frame_buffer.py
import threading
from typing import Optional

from .models import StreamFrame


class FrameBuffer:
    """
    Thread-safe buffer that always stores only the latest frame.

    - update(frame): store a new frame (overwrites previous one)
    - get_latest(): return the most recent frame or None if nothing yet
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest: Optional[StreamFrame] = None

    def update(self, frame: StreamFrame) -> None:
        """Store a new frame, overwriting any previous frame."""
        with self._lock:
            self._latest = frame

    def get_latest(self) -> Optional[StreamFrame]:
        """
        Return the most recent frame, or None if no frame has been stored yet.
        """
        with self._lock:
            return self._latest
