"""Domain models for building energy analytics.

This package contains all domain models with business logic methods
for building energy analysis workflows.
"""

from .building import BuildingData
from .utility_bills import UtilityBillData, CalendarizedData, EnergyAggregation, FuelAggregation
from .location import LocationInfo
from .weather import WeatherData, WeatherSeries, WeatherStation
# Import result models from their new domain-specific modules
from better_lbnl_os.core.changepoint import ChangePointModelResult
from better_lbnl_os.core.savings import SavingsEstimate
from better_lbnl_os.core.recommendations import EEMeasureRecommendation
from .benchmarking import (
    BenchmarkStatistics,
    CoefficientBenchmarkResult,
    EnergyTypeBenchmarkResult,
)

__all__ = [
    "BuildingData",
    "UtilityBillData",
    "CalendarizedData",
    "WeatherSeries",
    "EnergyAggregation",
    "FuelAggregation",
    "LocationInfo",
    "WeatherData",
    "WeatherStation",
    "ChangePointModelResult",
    "SavingsEstimate",
    "EEMeasureRecommendation",
    "BenchmarkStatistics",
    "CoefficientBenchmarkResult",
    "EnergyTypeBenchmarkResult",
]
