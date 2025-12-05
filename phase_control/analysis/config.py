from dataclasses import dataclass

from base_lib.models import Length, Range


@dataclass
class AnalysisConfig:
    wavelength_range: Range[Length]