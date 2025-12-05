from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from base_lib.models import Angle, AngleUnit, Prefix

STARTING_PHASE = Angle(0, AngleUnit.DEG)
CONVERSION_CONST = float(45/360)
CORRECTION_SIGN = -1

@dataclass
class PhaseCorrector:
    _correction_angle: Angle = Angle(0, AngleUnit.DEG)

    def update(self, phase: Angle) -> Angle:
        
        if np.abs(Angle(phase - STARTING_PHASE)) > Angle(10, AngleUnit.DEG):
            _correction_phase = Angle(phase - STARTING_PHASE)
            print("Correction needed!", _correction_phase.Deg)
        else:
            _correction_phase = Angle(0)
            
        self._correction_angle = Angle(CORRECTION_SIGN * self._convert_phase_to_angle(_correction_phase))
        
        return self._correction_angle

    def _convert_phase_to_angle(self, phase: Angle) -> Angle:
        return Angle(phase * CONVERSION_CONST)