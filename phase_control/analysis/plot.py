# phase_control/analysis/plot.py
import time
import threading

import numpy as np
import matplotlib.pyplot as plt

from phase_control.stream_io import StreamMeta, FrameBuffer


def run_plot(
    buffer: FrameBuffer,
    stop_event: threading.Event,
) -> None:
    """
    Plot loop running in the main thread.

    It:
    - uses 'meta' to set up the axes
    - repeatedly pulls the latest frame from 'buffer'
    - updates the plot until the window is closed or stop_event is set
    """
    # X-axis from wavelengths if available, otherwise pixel indices
    if buffer.meta.wavelengths is not None:
        x = np.array(meta.wavelengths, dtype=float)
        x_label = "Wavelength [nm]"
    else:
        x = np.arange(meta.num_pixels, dtype=float)
        x_label = "Pixel"

    # Matplotlib setup
    plt.ion()
    fig, ax = plt.subplots()

    y0 = np.zeros_like(x)
    (line,) = ax.plot(x, y0)

    ax.set_xlabel(x_label)
    ax.set_ylabel("Counts")
    ax.set_title(
        f"Live spectrum (Device {meta.device_index}, "
        f"{meta.exposure_ms:.1f} ms, avg={meta.average})"
    )

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()

    print("Live acquisition started (close the window or press Ctrl+C to stop).")

    try:
        while plt.fignum_exists(fig.number) and not stop_event.is_set():
            frame = buffer.get_latest()
            if frame is None:
                # No data yet, avoid busy-wait
                time.sleep(0.01)
                continue

            y = np.asarray(frame.counts, dtype=float)
            if y.size != x.size:
                # Safety check – skip malformed frames
                time.sleep(0.01)
                continue

            line.set_ydata(y)
            ax.relim()
            ax.autoscale_view()

            fig.canvas.draw()
            fig.canvas.flush_events()

            # Limit plot update rate (e.g. ~50 fps)
            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nLive plot interrupted by user.")
    finally:
        print("Live plot finished.")
        plt.ioff()
        plt.show()