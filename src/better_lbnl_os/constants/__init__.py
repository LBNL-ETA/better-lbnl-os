"""Constants package for building energy analytics.

Public, stable re-exports for enums, thresholds, energy factors, and mappings.
"""

from .enums import BuildingSpaceType, BenchmarkCategory
from .thresholds import (
    DEFAULT_R2_THRESHOLD,
    DEFAULT_CVRMSE_THRESHOLD,
    DEFAULT_SIGNIFICANT_PVAL,
)
from .energy import CONVERSION_TO_KWH
from .mappings import (
    normalize_space_type,
    space_type_to_benchmark_category,
    SPACE_TYPE_SYNONYMS,
)

__all__ = [
    # Enums
    "BuildingSpaceType",
    "BenchmarkCategory",
    # Thresholds
    "DEFAULT_R2_THRESHOLD",
    "DEFAULT_CVRMSE_THRESHOLD",
    "DEFAULT_SIGNIFICANT_PVAL",
    # Energy
    "CONVERSION_TO_KWH",
    # Mappings
    "normalize_space_type",
    "space_type_to_benchmark_category",
    "SPACE_TYPE_SYNONYMS",
]

