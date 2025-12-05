from pathlib import Path
import time
from matplotlib import pyplot as plt

from base_lib.models import Angle, Length, Prefix, Range, Time
from phase_control.Demo.data_io.data_loader import load_spectra
from phase_control.analysis.config import AnalysisConfig
from phase_control.analysis.phase_corrector import PhaseCorrector
from phase_control.analysis.phase_tracker import PhaseTracker
from phase_control.correction_io.elliptec_ell14 import ElliptecRotator
from phase_control.domain.models import Spectrum
from phase_control.domain.plotting import plot_model, plot_phase, plot_spectrogram


config = AnalysisConfig()

path = Path("Z:\\Droplets\\20251120\\Spectra_GA=26_DA=15p9\\spectrum-20-Nov-2025_121750 - both arms 10ms.txt")

spectra = load_spectra(path)
spectra_cut = [s.cut(config.wavelength_range) for s in spectra]

phase_tracker = PhaseTracker(config)
phase_corrector = PhaseCorrector()
#ell = ElliptecRotator()
phases = []
plt.ion()
fig, ax = plt.subplots()
fig.tight_layout()
fig.canvas.draw()
fig.canvas.flush_events()

for s in spectra:
    phase_tracker.update(s)
    
    if phase_tracker.current_phase is not None:
        delta = phase_corrector.update(phase_tracker.current_phase)
    else:
        delta = Angle(0)
        
    #ell.rotate(delta)
    time.sleep(5.0)
    print("Rotated:", delta)

    ax.clear()
    plot_spectrogram(ax, s)
    plot_model(ax, s.wavelengths_nm, phase_tracker._config)

    ax.relim()
    ax.autoscale_view()

    fig.canvas.draw()
    fig.canvas.flush_events()


ax.clear()
plot_phase(ax, phases)
fig.tight_layout()


