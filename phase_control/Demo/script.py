from pathlib import Path
from matplotlib import pyplot as plt

from base_lib.models import Length, Prefix, Range
from phase_control.Demo.data_io.data_loader import load_spectra
from phase_control.analysis.config import AnalysisConfig
from phase_control.analysis.phase_corrector import PhaseCorrector
from phase_control.domain.plotting import plot_spectrogram


config = AnalysisConfig(
    Range(Length(790, Prefix.NANO), Length(810, Prefix.NANO))
    )

path = Path("Z:\\Droplets\\20251120\\Spectra_GA=26_DA=15p9\\spectrum-20-Nov-2025_121750 - both arms 10ms.txt")

spectra = load_spectra(path)
phase_correcter = PhaseCorrector(config)
phases = []

for s in spectra:
    phase_correcter.update(s)
    phases.append(phase_correcter.current_phase)

fig, ax = plt.subplots(figsize=(8, 4))
plot_spectrogram(ax, dwd)

fig.tight_layout()
plt.show()