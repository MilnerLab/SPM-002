from pathlib import Path
from typing import List

from phase_control.domain.models import Spectrogram

def load_spectrograms(path: str | Path) -> List[Spectrogram]:
    """
    Read the spectrum text file and return a list of Spectrogram instances.
    Each data row (after the header) becomes one Spectrogram.
    """
    path = Path(path)

    with path.open(encoding="utf-8", errors="replace") as f:
        # 1) Skip metadata lines
        next(f)  # "Photon Control R&D ..."
        next(f)  # "Reference Spectrum"
        next(f)  # "Dark Spectrum"

        # 2) Header line with wavelengths
        header_cols = [c for c in next(f).strip().split("\t") if c]
        # Columns 0–2: Date, Time, Exposure (ms)
        wavelength_values = [float(c) for c in header_cols[3:]]

        spectrograms: List[Spectrogram] = []

        # 3) Each remaining line is one spectrum
        for line in f:
            line = line.strip()
            if not line:
                continue

            cols = [c for c in line.split("\t") if c]
            if len(cols) < 4:
                # Skip malformed lines
                continue

            # 0=Date, 1=Time, 2=Exposure(ms), from 3 onward: counts
            count_values = [int(c) for c in cols[3:]]

            if len(count_values) != len(wavelength_values):
                raise ValueError("Should be the same size.")

            spectrograms.append(
                Spectrogram.from_raw_data(wavelength_values, count_values)
            )

    return spectrograms
