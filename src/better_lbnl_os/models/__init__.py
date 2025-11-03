"""Domain models for building energy analytics.

This package contains all domain models with business logic methods
for building energy analysis workflows.
"""

from .benchmarking import (
    BenchmarkStatistics,
    CoefficientBenchmarkResult,
    EnergyTypeBenchmarkResult,
)
from .building import BuildingData
from .location import LocationInfo, LocationSummary
from .recommendations import (
    EEMeasureRecommendation,
    EERecommendationResult,
    InefficiencySymptom,
)
from .utility_bills import CalendarizedData, EnergyAggregation, FuelAggregation, UtilityBillData
from .weather import WeatherData, WeatherSeries, WeatherStation

# Import result models from their new domain-specific modules
# These must be imported AFTER the local imports to avoid circular dependencies
from better_lbnl_os.core.changepoint import ChangePointModelResult
from better_lbnl_os.core.savings import SavingsEstimate

__all__ = [
    "BenchmarkStatistics",
    "BuildingData",
    "CalendarizedData",
    "ChangePointModelResult",
    "CoefficientBenchmarkResult",
    "EEMeasureRecommendation",
    "EERecommendationResult",
    "EnergyAggregation",
    "EnergyTypeBenchmarkResult",
    "FuelAggregation",
    "InefficiencySymptom",
    "LocationInfo",
    "LocationSummary",
    "SavingsEstimate",
    "UtilityBillData",
    "WeatherData",
    "WeatherSeries",
    "WeatherStation",
]
