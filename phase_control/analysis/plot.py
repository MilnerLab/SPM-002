# analysis/plot.py
import numpy as np
import matplotlib.pyplot as plt

from phase_control.stream_io.stream_client import SpectrometerStreamClient



def run_plot() -> None:
    """
    Start the 32-bit acquisition process, receive spectra via the stream client,
    and display a live plot using 64-bit NumPy/Matplotlib.
    """
    with SpectrometerStreamClient() as client:
        meta = client.meta

        if meta.wavelengths is not None:
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
            for frame in client.frames():
                # If the window has been closed, stop the loop
                if not plt.fignum_exists(fig.number):
                    break

                y = np.array(frame.counts, dtype=float)
                if y.size != x.size:
                    # unexpected size mismatch – skip frame
                    continue

                line.set_ydata(y)
                ax.relim()
                ax.autoscale_view()

                fig.canvas.draw()
                fig.canvas.flush_events()

        except KeyboardInterrupt:
            print("\nLive plot interrupted by user.")

        print("Live plot finished.")
        plt.ioff()
        plt.show()


def main() -> None:
    run_plot()


if __name__ == "__main__":
    main()
