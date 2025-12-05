from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from base_lib.models import Angle, AngleUnit, Prefix

STARTING_PHASE = Angle(0, AngleUnit.DEG)

@dataclass
class PhaseCorrector:
    correction_phase: Angle = Angle(0, AngleUnit.DEG)

    def update(self, phase: Angle) -> Angle:
        
        if np.abs(Angle(phase - STARTING_PHASE)) > Angle(10, AngleUnit.DEG):
                self.correction_phase = Angle(phase - STARTING_PHASE)
                print("Correction needed!")
        else:
            self.correction_phase = Angle(0)

        return self.correction_phase

