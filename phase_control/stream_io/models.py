# phase_control/stream_io/models.py
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StreamMeta:
    """
    Static information about the spectrometer stream.
    Sent once as the initial 'meta' JSON object.
    """
    device_index: int
    num_pixels: int
    wavelengths: Optional[List[float]]
    exposure_ms: float
    average: int
    dark_subtraction: int


@dataclass
class StreamFrame:
    """
    One spectrum frame from the acquisition process.
    Corresponds to a 'frame' JSON object.
    """
    timestamp: str          # ISO-8601 string
    device_index: int
    counts: List[int]
