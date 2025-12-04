from pathlib import Path
from matplotlib import pyplot as plt

from phase_control.Demo.data_io.data_loader import load_spectrograms
from phase_control.domain.plotting import plot_spectrogram


path = Path("Z:\\Droplets\\20251120\\Spectra_GA=26_DA=15p9\\spectrum-20-Nov-2025_121750 - both arms 10ms.txt")

de = load_spectrograms(path)

dwd = de[-1]

fig, ax = plt.subplots(figsize=(8, 4))
plot_spectrogram(ax, dwd)

fig.tight_layout()
plt.show()