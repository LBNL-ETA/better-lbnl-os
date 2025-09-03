"""Domain models for building energy analytics.

This package contains all domain models with business logic methods
for building energy analysis workflows.
"""

from .building import BuildingData
from .utility_bills import UtilityBillData, CalendarizedData, EnergyAggregation, FuelAggregation
from .location import LocationInfo
from .weather import WeatherData, WeatherSeries, WeatherStation
from .results import (
    ChangePointModelResult,
    BenchmarkResult,
    SavingsEstimate,
    EEMeasureRecommendation,
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
    "BenchmarkResult",
    "SavingsEstimate",
    "EEMeasureRecommendation",
]
