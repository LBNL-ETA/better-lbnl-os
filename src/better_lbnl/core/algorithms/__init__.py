"""Pure mathematical algorithms for building energy analysis."""

from better_lbnl.core.algorithms.changepoint import (
    fit_changepoint_model,
    fit_3p_heating,
    fit_3p_cooling,
    fit_5p_model,
)
from better_lbnl.core.algorithms.statistics import (
    calculate_r_squared,
    calculate_cvrmse,
    calculate_nmbe,
    calculate_mape,
)

__all__ = [
    # Change-point models
    "fit_changepoint_model",
    "fit_3p_heating",
    "fit_3p_cooling",
    "fit_5p_model",
    # Statistical metrics
    "calculate_r_squared",
    "calculate_cvrmse",
    "calculate_nmbe",
    "calculate_mape",
]