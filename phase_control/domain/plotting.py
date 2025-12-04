from typing import Optional
from matplotlib.axes import Axes

from base_lib.models import Prefix
from phase_control.domain.models import Spectrogram

def plot_spectrogram(ax: Axes, spec: Spectrogram, label: Optional[str] = None) -> None:
    
    wavelengths_nm = [w.value(Prefix.NANO) for w in spec.wavelengths]

    ax.plot(wavelengths_nm, spec.intensity, label=label)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Normalized intensity (a.u.)")

    if label is not None:
        ax.legend()
