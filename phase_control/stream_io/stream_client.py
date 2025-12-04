# stream_io/stream_client.py
import json
import os
from pathlib import Path
import subprocess
from dataclasses import dataclass
from typing import Iterator, List, Optional

from acquisition.config import PYTHON32_PATH


@dataclass
class StreamMeta:
    """
    Static information about the spectrometer stream.
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
    One spectrum frame received from the acquisition process.
    """
    timestamp: str          # ISO-8601 string
    device_index: int
    counts: List[int]


class SpectrometerStreamClient:
    """
    Client for the 32-bit acquisition JSON stream.

    Responsibilities:
    - start the 32-bit Python acquisition process
    - read a single 'meta' JSON object
    - provide an iterator over 'frame' JSON objects
    - handle clean shutdown of the child process

    This class does NOT:
    - do any analysis
    - do any plotting
    """

    def __init__(
        self,
    ) -> None:
        """
        Parameters
        ----------
        python32_path:
            Path to the 32-bit Python interpreter. If None, the environment
            variable 'PYTHON32_PATH' is used. If that is also missing, you
            must adapt the default path below.
        """
        self.python32_path = PYTHON32_PATH

        self._proc: Optional[subprocess.Popen[str]] = None
        self._meta: Optional[StreamMeta] = None

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def meta(self) -> StreamMeta:
        if self._meta is None:
            raise RuntimeError("StreamMeta is not available. Did you call start()? "
                               "Or are you using the context manager?")
        return self._meta

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "SpectrometerStreamClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

    # ------------------------------------------------------------------ #
    # Process management
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """
        Start the 32-bit acquisition process and read the initial meta frame.
        """
        if self._proc is not None:
            raise RuntimeError("Acquisition process is already running.")

        repo_root = Path(__file__).resolve().parents[2]
        script_path = repo_root / "acquisition" / "json_stream_server.py"

        proc = subprocess.Popen(
            [self.python32_path, script_path],
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.PIPE,   # you can log/debug this if needed
            text=True,                # line-based text mode
            bufsize=1,                # line-buffered
        )
        self._proc = proc

        if proc.stdout is None:
            raise RuntimeError("Failed to open stdout from acquisition process.")

        # Read meta line
        meta_line = proc.stdout.readline()
        if not meta_line:
            # Try to collect stderr to give a helpful message
            stderr_msg = ""
            if proc.stderr is not None:
                stderr_msg = proc.stderr.read()
            raise RuntimeError(
                f"Acquisition process terminated before sending meta data.\n"
                f"stderr:\n{stderr_msg}"
            )

        meta_raw = json.loads(meta_line)
        if meta_raw.get("type") != "meta":
            raise RuntimeError(f"Expected meta frame, got: {meta_raw!r}")

        self._meta = StreamMeta(
            device_index=meta_raw["device_index"],
            num_pixels=meta_raw["num_pixels"],
            wavelengths=meta_raw["wavelengths"],  # may be None
            exposure_ms=meta_raw["exposure_ms"],
            average=meta_raw["average"],
            dark_subtraction=meta_raw["dark_subtraction"],
        )

    def stop(self) -> None:
        """
        Stop the acquisition process if it is running.
        """
        proc = self._proc
        self._proc = None

        if proc is None:
            return

        if proc.poll() is not None:
            # already exited
            return

        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    # ------------------------------------------------------------------ #
    # Streaming API
    # ------------------------------------------------------------------ #

    def frames(self) -> Iterator[StreamFrame]:
        """
        Iterate over frames from the acquisition process.

        This generator yields StreamFrame objects until the acquisition
        process finishes or an error occurs.
        """
        if self._proc is None or self._proc.stdout is None:
            raise RuntimeError("Acquisition process is not running. Call start() first "
                               "or use 'with SpectrometerStreamClient() as client:'.")

        proc = self._proc
        for line in proc.stdout: # type: ignore
            line = line.strip()
            if not line:
                continue

            frame_raw = json.loads(line)
            if frame_raw.get("type") != "frame":
                # ignore other messages
                continue

            yield StreamFrame(
                timestamp=frame_raw["timestamp"],
                device_index=frame_raw["device_index"],
                counts=frame_raw["counts"],
            )
