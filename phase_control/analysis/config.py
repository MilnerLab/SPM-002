from dataclasses import dataclass, fields, asdict
import inspect
from typing import Any, Callable, TypeVar, get_type_hints

import lmfit
import numpy as np

from base_lib.models import Angle, Length, Prefix, Range

T = TypeVar("T", bound="FitParameter")

@dataclass
class FitParameter:
    carrier_wavelength: Length = Length(802.38, Prefix.NANO)
    starting_wavelength: Length = Length(808.352, Prefix.NANO)
    bandwidth: Length = Length(7.4728, Prefix.NANO)
    baseline: float = 0.3338
    phase: Angle = Angle(-3.34)
    acceleration: float = 0.0979 * np.pi * 2
    
    def to_fit_kwargs(self, func: Callable[..., Any]) -> dict[str, float]:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())[1:]  

        type_converters = {
            Length: lambda l: l.value(Prefix.NANO),
            Angle:  lambda a: a.Rad,
            float:  float,
        }

        kwargs: dict[str, float] = {}
        type_hints = get_type_hints(type(self))

        for name in param_names:
            val = getattr(self, name)
            field_type = type_hints.get(name, type(val))
            conv = type_converters.get(field_type, lambda v: v)
            kwargs[name] = conv(val)

        return kwargs
    
    @classmethod
    def from_fit_result(cls: type[T], base: T, result: lmfit.model.ModelResult) -> T:
        best = result.best_values  

        type_converters: dict[type[Any], Callable[[float], Any]] = {
            Length: lambda v: Length(v, Prefix.NANO),
            Angle:  lambda v: Angle(v),
            float:  float,
        }

        type_hints: dict[str, type[Any]] = get_type_hints(cls)

        kwargs: dict[str, Any] = {}

        for f in fields(cls):
            name = f.name

            if name in best:
                field_type = type_hints.get(name, float)
                conv = type_converters.get(field_type, lambda v: v)
                kwargs[name] = conv(best[name])
            else:
                kwargs[name] = getattr(base, name)

        return cls(**kwargs)

@dataclass
class AnalysisConfig(FitParameter):
    wavelength_range: Range[Length] = Range(Length(800, Prefix.NANO), Length(805, Prefix.NANO))
