from __future__ import annotations 
from dataclasses import dataclass

from base_lib.models import Length, Prefix

@dataclass
class Spectrum:
    wavelengths: list[Length]
    intensity: list[float]

    @classmethod
    def from_raw_data(
        cls,
        wavelengths: list[float],
        counts: list[int],
    ) -> Spectrum: 
        total = sum(counts)
        if total == 0:
            raise ValueError("counts should not be 0.")
        intensities = [c / total for c in counts]
        
        return cls([Length(w, Prefix.NANO) for w in wavelengths], intensities)
