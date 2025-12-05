import numpy as np
from base_lib.models import Angle
from phase_control.analysis.config import AnalysisConfig
from phase_control.domain.models import Spectrum


class PhaseCorrector():
    current_phase: Angle | None = None
    
    def __init__(self, config: AnalysisConfig) -> None:
        self._config = config
    
    def update(self, spectrum: Spectrum) -> None:
        self.current_phase = Angle(np.pi)