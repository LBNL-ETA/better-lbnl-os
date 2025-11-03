"""Shim module for weather calculations.

Functions have moved to `better_lbnl_os.utils.calculations`. This module
re-exports them for backwards compatibility.
"""

import warnings

from better_lbnl_os.utils.calculations import *  # noqa: F403

warnings.warn(
    "better_lbnl_os.core.weather.calculations has moved to better_lbnl_os.utils.calculations",
    DeprecationWarning,
    stacklevel=2,
)
