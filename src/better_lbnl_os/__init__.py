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
from better_lbnl_os.core.benchmarking import (
    benchmark_building,
    create_statistics_from_models,
    calculate_portfolio_statistics,
    get_reference_statistics,
    benchmark_with_reference,
    list_available_reference_statistics,
)
from better_lbnl_os.core.recommendations import (
    detect_symptoms,
    map_symptoms_to_measures,
    recommend_ee_measures,
    BETTER_MEASURES,
)

# Domain models with behavior (new stable path)
from better_lbnl_os.models import (
    BuildingData,
    UtilityBillData,
    WeatherData,
)
# Result models from their domain-specific modules
from better_lbnl_os.core.changepoint import ChangePointModelResult
from better_lbnl_os.core.savings import (
    SavingsEstimate,
    FuelSavingsResult,
    CombinedSavingsSummary,
    SavingsSummary,
    estimate_savings_for_fuel,
    estimate_savings,
)
from better_lbnl_os.models.benchmarking import (
    BenchmarkResult,
    BenchmarkStatistics,
    CoefficientBenchmarkResult,
    EnergyTypeBenchmarkResult,
)
from better_lbnl_os.models.recommendations import (
    InefficiencySymptom,
    EEMeasureRecommendation,
    EERecommendationResult,
)

# Services for orchestration
from better_lbnl_os.core.services import (
    BuildingAnalyticsService,
    PortfolioBenchmarkService,
)
from better_lbnl_os.core.pipeline import (
    prepare_model_data,
    fit_calendarized_models,
    fit_models_from_inputs,
    get_weather_for_bills,
    fit_models_with_auto_weather,
)
from better_lbnl_os.models import (
    CalendarizedData,
    WeatherSeries,
    EnergyAggregation,
    FuelAggregation,
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
    # Benchmarking algorithms
    "benchmark_building",
    "create_statistics_from_models",
    "calculate_portfolio_statistics",
    "get_reference_statistics",
    "benchmark_with_reference",
    "list_available_reference_statistics",
    # Recommendation algorithms
    "detect_symptoms",
    "map_symptoms_to_measures",
    "recommend_ee_measures",
    "BETTER_MEASURES",
    # Domain models
    "BuildingData",
    "UtilityBillData",
    "WeatherData",
    # Result models
    "ChangePointModelResult",
    "SavingsEstimate",
    "FuelSavingsResult",
    "CombinedSavingsSummary",
    "SavingsSummary",
    "estimate_savings_for_fuel",
    "estimate_savings",
    # Benchmarking models
    "BenchmarkResult",
    "BenchmarkStatistics",
    "CoefficientBenchmarkResult",
    "EnergyTypeBenchmarkResult",
    # Recommendation models
    "InefficiencySymptom",
    "EEMeasureRecommendation",
    "EERecommendationResult",
    # Services
    "BuildingAnalyticsService",
    "PortfolioBenchmarkService",
    # Pipeline helpers
    "prepare_model_data",
    "fit_calendarized_models",
    "fit_models_from_inputs",
    "get_weather_for_bills",
    "fit_models_with_auto_weather",
    # Calendarized models
    "CalendarizedData",
    "WeatherSeries",
    "EnergyAggregation",
    "FuelAggregation",
]
