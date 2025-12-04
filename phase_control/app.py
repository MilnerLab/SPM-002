# phase_control/app.py
import threading
from typing import NoReturn

from phase_control.stream_io import (
    SpectrometerStreamClient,
    FrameBuffer,
    StreamFrame,
    StreamMeta,
)
from phase_control.analysis.plot import run_plot


def reader_loop(
    client: SpectrometerStreamClient,
    buffer: FrameBuffer,
    stop_event: threading.Event,
) -> None:
    """
    Background thread function.

    - consumes frames from the SpectrometerStreamClient
    - updates the FrameBuffer with the latest frame
    - exits when stop_event is set or the stream ends
    """
    try:
        for frame in client.frames():
            if stop_event.is_set():
                break
            buffer.update(frame)
    finally:
        # Make sure the process is stopped even if the loop ends
        client.stop()


def main() -> None:
    """
    Application entry point:

    - start stream client (32-bit acquisition process)
    - create frame buffer
    - start reader thread
    - run plot in main thread
    """
    client = SpectrometerStreamClient()
    meta: StreamMeta = client.start()

    buffer = FrameBuffer()
    stop_event = threading.Event()

    reader = threading.Thread(
        target=reader_loop,
        args=(client, buffer, stop_event),
        name="SpectrometerReaderThread",
        daemon=True,
    )
    reader.start()

    try:
        # Run plotting in the main thread
        run_plot(meta=meta, buffer=buffer, stop_event=stop_event)
    finally:
        # Tell reader to stop and clean up
        stop_event.set()
        reader.join(timeout=2.0)
        client.stop()


if __name__ == "__main__":
    main()
