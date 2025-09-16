"""Constants package for building energy analytics.

Public, stable re-exports for enums, thresholds, energy factors, and mappings.
"""

from .enums import BuildingSpaceType
from .thresholds import (
    DEFAULT_R2_THRESHOLD,
    DEFAULT_CVRMSE_THRESHOLD,
    DEFAULT_SIGNIFICANT_PVAL,
)
from .energy import CONVERSION_TO_KWH
from .mappings import (
    normalize_space_type,
    space_type_to_building_space_type,
    SPACE_TYPE_SYNONYMS,
)
from .template_parsing import SQFT_TO_SQM
from .measures import TOP_LEVEL_EE_MEASURES

__all__ = [
    # Enums
    "BuildingSpaceType",
    # Thresholds
    "DEFAULT_R2_THRESHOLD",
    "DEFAULT_CVRMSE_THRESHOLD",
    "DEFAULT_SIGNIFICANT_PVAL",
    # Energy
    "CONVERSION_TO_KWH",
    # Mappings
    "normalize_space_type",
    "space_type_to_building_space_type",
    "SPACE_TYPE_SYNONYMS",
    # Templates
    "SQFT_TO_SQM",
    # Measures
    "TOP_LEVEL_EE_MEASURES",
]

