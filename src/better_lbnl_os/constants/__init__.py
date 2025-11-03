"""Constants package for building energy analytics.

Public, stable re-exports for enums, thresholds, energy factors, and mappings.
"""

from .building_types import BuildingSpaceType, space_type_to_benchmark_category
from .energy import (
    CONVERSION_TO_KWH,
    FuelType,
    FuelUnit,
    normalize_fuel_type,
    normalize_fuel_unit,
)
from .mappings import (
    SPACE_TYPE_SYNONYMS,
    normalize_space_type,
    space_type_to_building_space_type,
)
from .measures import TOP_LEVEL_EE_MEASURES
from .recommendations import SYMPTOM_COEFFICIENTS, SYMPTOM_DESCRIPTIONS
from .savings import MINIMUM_UTILITY_MONTHS, PLOT_EXCEEDANCE
from .template_parsing import SQFT_TO_SQM
from .thresholds import (
    DEFAULT_CVRMSE_THRESHOLD,
    DEFAULT_R2_THRESHOLD,
    DEFAULT_SIGNIFICANT_PVAL,
)

__all__ = [
    # Energy
    "CONVERSION_TO_KWH",
    "DEFAULT_CVRMSE_THRESHOLD",
    # Thresholds
    "DEFAULT_R2_THRESHOLD",
    "DEFAULT_SIGNIFICANT_PVAL",
    "MINIMUM_UTILITY_MONTHS",
    "PLOT_EXCEEDANCE",
    "SPACE_TYPE_SYNONYMS",
    # Templates
    "SQFT_TO_SQM",
    # Recommendation metadata
    "SYMPTOM_COEFFICIENTS",
    "SYMPTOM_DESCRIPTIONS",
    # Measures
    "TOP_LEVEL_EE_MEASURES",
    # Enums
    "BuildingSpaceType",
    "FuelType",
    "FuelUnit",
    "normalize_fuel_type",
    "normalize_fuel_unit",
    # Mappings
    "normalize_space_type",
    "space_type_to_benchmark_category",
    "space_type_to_building_space_type",
]
