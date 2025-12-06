from dataclasses import dataclass, field
import math
from typing import Optional

import numpy as np

from base_lib.models import Angle, AngleUnit, Prefix

STARTING_PHASE = Angle(0, AngleUnit.DEG)
PHASE_TOLERANCE = Angle(10, AngleUnit.DEG)

# grober Startwert: 1° HWP ändert die Fit-Phase um ca. 4°
# → HWP_deg = - phase_deg / 4
CONVERSION_CONST = 1.0 / 4.0      # deg_HWP pro deg_Phase
CORRECTION_SIGN = -1      

from dataclasses import dataclass

@dataclass
class PhaseCorrector:
    _correction_angle: Angle = Angle(0, AngleUnit.DEG)

    def update(self, phase: Angle) -> Angle:
        """
        phase: gefittete Phase des sin²-Terms als Angle.
        Angle selbst ist 2π-periodisch, deshalb wickeln wir hier explizit auf π.
        """
        phase_wrapped = self._wrap_phase_pi(phase)

        phase_error = Angle(phase_wrapped - STARTING_PHASE)

        if np.abs(phase_error) > PHASE_TOLERANCE:
            correction_phase = phase_error
            print("Correction needed!", correction_phase.Deg)
        else:
            correction_phase = Angle(0)

        self._correction_angle = self._convert_phase_to_hwp(correction_phase)
        return self._correction_angle

    @staticmethod
    def _wrap_phase_pi(phase: Angle) -> Angle:
        """
        Wickelt die Phase auf [-π/2, π/2), damit Lösungen,
        die sich um π unterscheiden (0 und π), als gleich behandelt werden.
        """
        pi = math.pi
        rad = phase.Rad
        wrapped = (rad + 0.5 * pi) % pi - 0.5 * pi
        return Angle(wrapped, AngleUnit.RAD)

    @staticmethod
    def _convert_phase_to_hwp(phase: Angle) -> Angle:
        """
        Phasefehler (sin²-Phase) → HWP-Winkel.

        Näherung: Δphase ≈ 4 * Δalpha_HWP
        → Δalpha_HWP = - Δphase / 4
        """
        phase_deg = phase.Deg
        hwp_deg = CORRECTION_SIGN * phase_deg * CONVERSION_CONST
        return Angle(hwp_deg, AngleUnit.DEG)
