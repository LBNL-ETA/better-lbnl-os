"""BETTER-LBNL: Building Energy Analytics Library.

Open-source Python library for building energy analytics, extracted from
BETTER (Building Efficiency Targeting Tool for Energy Retrofits).

This library provides:
- Change-point model fitting for energy usage analysis
- Building performance benchmarking
- Energy savings estimation
- Energy efficiency measure recommendations
"""

__version__ = "0.1.0"
__author__ = "Han Li"
__email__ = "hanli@lbl.gov"

# Core algorithms - pure functions
from better_lbnl_os.core.changepoint import (
    fit_changepoint_model,
    calculate_cvrmse,
    calculate_r_squared,
)

# Domain models with behavior
from better_lbnl_os.data.models import (
    BuildingData,
    UtilityBillData,
    WeatherData,
    ChangePointModelResult,
    BenchmarkResult,
    SavingsEstimate,
)

# Services for orchestration
from better_lbnl_os.data.services import (
    BuildingAnalyticsService,
    PortfolioBenchmarkService,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Core algorithms
    "fit_changepoint_model",
    "calculate_cvrmse",
    "calculate_r_squared",
    # Domain models
    "BuildingData",
    "UtilityBillData",
    "WeatherData",
    "ChangePointModelResult",
    "BenchmarkResult",
    "SavingsEstimate",
    # Services
    "BuildingAnalyticsService",
    "PortfolioBenchmarkService",
]
