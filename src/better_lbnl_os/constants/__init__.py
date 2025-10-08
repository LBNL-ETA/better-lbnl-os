"""Constants package for building energy analytics.

Public, stable re-exports for enums, thresholds, energy factors, and mappings.
"""

from .building_types import BuildingSpaceType, space_type_to_benchmark_category
from .thresholds import (
    DEFAULT_R2_THRESHOLD,
    DEFAULT_CVRMSE_THRESHOLD,
    DEFAULT_SIGNIFICANT_PVAL,
)
from .energy import (
    CONVERSION_TO_KWH,
    FuelType,
    FuelUnit,
    normalize_fuel_type,
    normalize_fuel_unit,
)

from .mappings import (
    normalize_space_type,
    space_type_to_building_space_type,
    SPACE_TYPE_SYNONYMS,
)
from .template_parsing import SQFT_TO_SQM
from .measures import TOP_LEVEL_EE_MEASURES
from .recommendations import SYMPTOM_COEFFICIENTS, SYMPTOM_DESCRIPTIONS

from .savings import MINIMUM_UTILITY_MONTHS, PLOT_EXCEEDANCE

__all__ = [
    # Enums
    "BuildingSpaceType",
    "space_type_to_benchmark_category",
    # Thresholds
    "DEFAULT_R2_THRESHOLD",
    "DEFAULT_CVRMSE_THRESHOLD",
    "DEFAULT_SIGNIFICANT_PVAL",
    # Energy
    "CONVERSION_TO_KWH",
    "FuelType",
    "FuelUnit",
    "normalize_fuel_type",
    "normalize_fuel_unit",
    # Mappings
    "normalize_space_type",
    "space_type_to_building_space_type",
    "SPACE_TYPE_SYNONYMS",
    # Templates
    "SQFT_TO_SQM",
    # Measures
    "TOP_LEVEL_EE_MEASURES",
    # Recommendation metadata
    "SYMPTOM_COEFFICIENTS",
    "SYMPTOM_DESCRIPTIONS",
    "MINIMUM_UTILITY_MONTHS",
    "PLOT_EXCEEDANCE",
]

