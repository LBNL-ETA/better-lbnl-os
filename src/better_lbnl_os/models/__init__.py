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
from .benchmarking import (
    BenchmarkStatistics,
    CoefficientBenchmarkResult,
    EnergyTypeBenchmarkResult,
)
from .recommendations import (
    InefficiencySymptom,
    EEMeasureRecommendation,
    EERecommendationResult,
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
    "BenchmarkStatistics",
    "CoefficientBenchmarkResult",
    "EnergyTypeBenchmarkResult",
    "InefficiencySymptom",
    "EEMeasureRecommendation",
    "EERecommendationResult",
]
