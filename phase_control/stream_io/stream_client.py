# phase_control/stream_io/stream_client.py
"""
Low-level stream client for the 32-bit acquisition process.

Responsibilities:
- start the 32-bit Python process running `acquisition.json_stream_server`
- read the initial 'meta' JSON object
- provide an iterator over 'frame' JSON objects
- stop/terminate the process when done

This module does NOT:
- start any threads
- manage any buffers or queues
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Iterator, Optional

from acquisition.config import PYTHON32_PATH
from .models import StreamMeta, StreamFrame


class SpectrometerStreamClient:
    """
    Stream client for the JSON output of the 32-bit acquisition process.
    """

    def __init__(self, python32_path: Optional[str] = None) -> None:
        """
        Parameters
        ----------
        python32_path:
            Path to the 32-bit Python interpreter.

            Resolution priority:
            1. explicit python32_path argument
            2. environment variable 'PYTHON32_PATH'
            3. acquisition.config.PYTHON32_PATH
        """
        self.python32_path = (
            python32_path
            or os.environ.get("PYTHON32_PATH")
            or PYTHON32_PATH
        )

        self._proc: Optional[subprocess.Popen[str]] = None
        self._meta: Optional[StreamMeta] = None

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def meta(self) -> StreamMeta:
        """
        Static meta information. Only valid after start() has been called.
        """
        if self._meta is None:
            raise RuntimeError("StreamMeta not available. Did you call start()?")

        return self._meta

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> StreamMeta:
        """
        Start the 32-bit acquisition process and read the 'meta' frame.

        Returns
        -------
        StreamMeta
            Static meta information describing the stream.
        """
        if self._proc is not None:
            raise RuntimeError("Acquisition process is already running.")

        repo_root = Path(__file__).resolve().parents[2]  # .../SPM-002

        proc = subprocess.Popen(
            [self.python32_path, "-m", "acquisition.json_stream_server"],
            cwd=str(repo_root),          # acquisition package visible for -m
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,                   # line-buffered
        )
        self._proc = proc

        if proc.stdout is None:
            raise RuntimeError("Failed to open stdout from acquisition process.")

        # Read one line (meta)
        meta_line = proc.stdout.readline()
        if not meta_line:
            stderr_msg = ""
            if proc.stderr is not None:
                stderr_msg = proc.stderr.read()
            raise RuntimeError(
                "Acquisition process terminated before sending meta data.\n"
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

        return self._meta

    def frames(self) -> Iterator[StreamFrame]:
        """
        Iterate over frames from the acquisition process.

        This is a blocking iterator. It should normally be called from a
        background thread. It does NOT do any buffering itself.
        """
        proc = self._proc
        if proc is None or proc.stdout is None:
            raise RuntimeError("Acquisition process is not running. Call start() first.")

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            try:
                frame_raw = json.loads(line)
            except json.JSONDecodeError:
                continue

            if frame_raw.get("type") != "frame":
                continue  # ignore meta or other messages

            yield StreamFrame(
                timestamp=frame_raw["timestamp"],
                device_index=frame_raw["device_index"],
                counts=frame_raw["counts"],
            )

    def stop(self) -> None:
        """
        Terminate the acquisition process if it is still running.
        """
        proc = self._proc
        self._proc = None

        if proc is None:
            return

        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
