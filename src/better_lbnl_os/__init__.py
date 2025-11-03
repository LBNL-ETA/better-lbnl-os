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
from better_lbnl_os.core.benchmarking import (
    benchmark_building,
    benchmark_with_reference,
    calculate_portfolio_statistics,
    create_statistics_from_models,
    get_reference_statistics,
    list_available_reference_statistics,
)

# Result models from their domain-specific modules
from better_lbnl_os.core.changepoint import (
    ChangePointModelResult,
    calculate_cvrmse,
    calculate_r_squared,
    fit_changepoint_model,
)
from better_lbnl_os.core.pipeline import (
    fit_calendarized_models,
    fit_models_from_inputs,
    fit_models_with_auto_weather,
    get_weather_for_bills,
    prepare_model_data,
    resolve_location,
)
from better_lbnl_os.core.recommendations import (
    BETTER_MEASURES,
    detect_symptoms,
    map_symptoms_to_measures,
    recommend_ee_measures,
)
from better_lbnl_os.core.savings import (
    CombinedSavingsSummary,
    FuelSavingsResult,
    SavingsEstimate,
    SavingsSummary,
    estimate_savings,
    estimate_savings_for_fuel,
)

# Services for orchestration
from better_lbnl_os.core.services import (
    BuildingAnalyticsService,
    PortfolioBenchmarkService,
)

# Domain models with behavior (new stable path)
from better_lbnl_os.models import (
    BuildingData,
    CalendarizedData,
    EnergyAggregation,
    FuelAggregation,
    UtilityBillData,
    WeatherData,
    WeatherSeries,
)
from better_lbnl_os.models.benchmarking import (
    BenchmarkResult,
    BenchmarkStatistics,
    CoefficientBenchmarkResult,
    EnergyTypeBenchmarkResult,
)
from better_lbnl_os.models.recommendations import (
    EEMeasureRecommendation,
    EERecommendationResult,
    InefficiencySymptom,
)

__all__ = [
    "BETTER_MEASURES",
    # Benchmarking models
    "BenchmarkResult",
    "BenchmarkStatistics",
    # Services
    "BuildingAnalyticsService",
    # Domain models
    "BuildingData",
    # Calendarized models
    "CalendarizedData",
    # Result models
    "ChangePointModelResult",
    "CoefficientBenchmarkResult",
    "CombinedSavingsSummary",
    "EEMeasureRecommendation",
    "EERecommendationResult",
    "EnergyAggregation",
    "EnergyTypeBenchmarkResult",
    "FuelAggregation",
    "FuelSavingsResult",
    # Recommendation models
    "InefficiencySymptom",
    "PortfolioBenchmarkService",
    "SavingsEstimate",
    "SavingsSummary",
    "UtilityBillData",
    "WeatherData",
    "WeatherSeries",
    "__author__",
    "__email__",
    # Version info
    "__version__",
    # Benchmarking algorithms
    "benchmark_building",
    "benchmark_with_reference",
    "calculate_cvrmse",
    "calculate_portfolio_statistics",
    "calculate_r_squared",
    "create_statistics_from_models",
    # Recommendation algorithms
    "detect_symptoms",
    "estimate_savings",
    "estimate_savings_for_fuel",
    "fit_calendarized_models",
    # Core algorithms
    "fit_changepoint_model",
    "fit_models_from_inputs",
    "fit_models_with_auto_weather",
    "get_reference_statistics",
    "get_weather_for_bills",
    "list_available_reference_statistics",
    "map_symptoms_to_measures",
    # Pipeline helpers
    "prepare_model_data",
    "recommend_ee_measures",
    "resolve_location",
]
