"""Domain models package (transitional).

This package re-exports domain models from the previous data.models module
to provide a stable import path during reorganization.
"""

from .building import BuildingData
from .utility import UtilityBillData
from .location import LocationInfo
from .weather import WeatherData, WeatherStation
from .results import (
    ChangePointModelResult,
    BenchmarkResult,
    SavingsEstimate,
    EEMeasureRecommendation,
)

__all__ = [
    "BuildingData",
    "UtilityBillData",
    "LocationInfo",
    "WeatherData",
    "WeatherStation",
    "ChangePointModelResult",
    "BenchmarkResult",
    "SavingsEstimate",
    "EEMeasureRecommendation",
]

