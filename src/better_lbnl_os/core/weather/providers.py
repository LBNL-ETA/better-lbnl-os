"""Weather data provider implementations (shim).

This module is kept for backward compatibility. Implementations are now
available under `better_lbnl_os.core.weather.providers`.
"""

import warnings

from .providers import NOAAProvider, OpenMeteoProvider  # re-export

warnings.warn(
    "better_lbnl_os.core.weather.providers is deprecated as a flat module. "
    "Use better_lbnl_os.core.weather.providers.open_meteo and .noaa or "
    "import from better_lbnl_os.core.weather.providers package.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["NOAAProvider", "OpenMeteoProvider"]
