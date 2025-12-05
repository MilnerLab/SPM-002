# phase_control/analysis/plot.py
import time
import threading

import numpy as np
import matplotlib.pyplot as plt

from base_lib.functions import usCFG_projection
from base_lib.models import Angle
from phase_control.analysis.config import AnalysisConfig
from phase_control.analysis.phase_corrector import PhaseCorrector
from phase_control.analysis.phase_tracker import PhaseTracker
from phase_control.correction_io.elliptec_ell14 import ElliptecRotator
from phase_control.domain.models import Spectrum
from phase_control.domain.plotting import plot_model, plot_spectrogram
from phase_control.stream_io import StreamMeta, FrameBuffer


def run_analysis(
    buffer: FrameBuffer,
    stop_event: threading.Event,
) -> None:
    
    config = AnalysisConfig()
    phase_tracker = PhaseTracker(config)
    phase_corrector = PhaseCorrector()
    ell = ElliptecRotator(max_address = "0") 
    
     # X-axis from wavelengths if available, otherwise pixel indices
    if buffer.meta.wavelengths is not None:
        x = np.array(buffer.meta.wavelengths, dtype=float)
        x_label = "Wavelength [nm]"
    else:
        x = np.arange(buffer.meta.num_pixels, dtype=float)
        x_label = "Pixel"

    spec0 = Spectrum.from_raw_data(x, np.ones_like(x)).cut(config.wavelength_range)
    # Matplotlib setup
    plt.ion()
    fig, ax = plt.subplots()

    (line,) = ax.plot(spec0.wavelengths_nm, spec0.intensity) #for current spectrum
    (line2,) = ax.plot(spec0.wavelengths_nm, spec0.intensity) #for current fit
    (line3,) = ax.plot(spec0.wavelengths_nm, spec0.intensity)

    first = True

    ax.set_xlabel(x_label)
    ax.set_ylabel("Counts")
    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()
    fig.gca().grid(axis = 'both')

    try:
        while plt.fignum_exists(fig.number) and not stop_event.is_set():
            current_spectrum = buffer.get_latest().cut(config.wavelength_range)
            if current_spectrum is None:
                # No data yet, avoid busy-wait
                time.sleep(0.01)
                continue

            phase_tracker.update(current_spectrum)

            '''
            if first:
                phase_tracker._config.phase = Angle(0)
                line3.set_ydata(usCFG_projection(current_spectrum.wavelengths_nm, **phase_tracker._config.to_fit_kwargs(usCFG_projection)))
                first = False
'''
    
            if phase_tracker.current_phase is None:
                raise ValueError("Should have a value.")
            
            correction_angle = phase_corrector.update(phase_tracker.current_phase)
            
            ell.rotate(correction_angle)
            print("Rotating", correction_angle)
            

            line.set_ydata(current_spectrum.intensity)
            line2.set_ydata(usCFG_projection(current_spectrum.wavelengths_nm, **phase_tracker._config.to_fit_kwargs(usCFG_projection)))
            
            ax.relim()
            ax.autoscale_view()

            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(0.02)
            

    except KeyboardInterrupt:
        print("\nLive plot interrupted by user.")
    finally:
        print("Live plot finished.")
        