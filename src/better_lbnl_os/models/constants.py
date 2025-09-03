"""Core constants and enumerations for the library (moved)."""

from __future__ import annotations
from enum import Enum

# Thresholds
DEFAULT_R2_THRESHOLD: float = 0.6
DEFAULT_CVRMSE_THRESHOLD: float = 0.5
DEFAULT_SIGNIFICANT_PVAL: float = 0.1

# Unit conversions to kWh
CONVERSION_TO_KWH: dict[tuple[str, str], float] = {
    ("ELECTRICITY", "kWh"): 1.0,
    ("ELECTRICITY", "MWh"): 1000.0,
    ("NATURAL_GAS", "therms"): 29.3,
    ("NATURAL_GAS", "ccf"): 29.3,
    ("NATURAL_GAS", "mcf"): 293.0,
    ("NATURAL_GAS", "MMBtu"): 293.0,
    ("FUEL_OIL", "gallons"): 40.6,
    ("PROPANE", "gallons"): 27.0,
    ("STEAM", "MLbs"): 293.0,
    ("STEAM", "therms"): 29.3,
}


class BuildingSpaceType(Enum):
    OFFICE = "Office"
    HOTEL = "Hotel"
    K12 = "K-12 School"
    MULTIFAMILY_HOUSING = "Multifamily Housing"
    WORSHIP_FACILITY = "Worship Facility"
    HOSPITAL = "Hospital (General Medical & Surgical)"
    MUSEUM = "Museum"
    BANK_BRANCH = "Bank Branch"
    COURTHOUSE = "Courthouse"
    DATA_CENTER = "Data Center"
    DISTRIBUTION_CENTER = "Distribution Center"
    FASTFOOD_RESTAURANT = "Fast Food Restaurant"
    FINANCIAL_OFFICE = "Financial Office"
    FIRE_STATION = "Fire Station"
    NON_REFRIGERATED_WAREHOUSE = "Non-Refrigerated Warehouse"
    POLICE_STATION = "Police Station"
    REFRIGERATED_WAREHOUSE = "Refrigerated Warehouse"
    RETAIL_STORE = "Retail Store"
    SELF_STORAGE_FACILITY = "Self-Storage Facility"
    SENIOR_CARE_COMMUNITY = "Senior Care Community"
    SUPERMARKET_GROCERY = "Supermarket/Grocery Store"
    RESTAURANT = "Restaurant"
    PUBLIC_LIBRARY = "Public Library"
    OTHER = "Other"


SPACE_TYPE_SYNONYMS: dict[str, str] = {
    "Retail": BuildingSpaceType.RETAIL_STORE.value,
    "School": BuildingSpaceType.K12.value,
    "Warehouse": BuildingSpaceType.NON_REFRIGERATED_WAREHOUSE.value,
    "Library": BuildingSpaceType.PUBLIC_LIBRARY.value,
}


def normalize_space_type(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Space type must be a string")
    candidate = value.strip()
    upper = candidate.upper().replace(" ", "_")
    if upper in BuildingSpaceType.__members__:
        return BuildingSpaceType[upper].value
    for st in BuildingSpaceType:
        if candidate == st.value:
            return st.value
    if candidate in SPACE_TYPE_SYNONYMS:
        return SPACE_TYPE_SYNONYMS[candidate]
    for key, val in SPACE_TYPE_SYNONYMS.items():
        if candidate.lower() == key.lower():
            return val
    raise ValueError(
        f"Space type must be one of {[st.value for st in BuildingSpaceType]}"
    )


class BenchmarkCategory(Enum):
    OFFICE = "OFFICE"
    HOTEL = "HOTEL"
    K12 = "K12"
    MULTIFAMILY_HOUSING = "MULTIFAMILY_HOUSING"
    WORSHIP_FACILITY = "WORSHIP_FACILITY"
    HOSPITAL = "HOSPITAL"
    MUSEUM = "MUSEUM"
    BANK_BRANCH = "BANK_BRANCH"
    COURTHOUSE = "COURTHOUSE"
    DATA_CENTER = "DATA_CENTER"
    DISTRIBUTION_CENTER = "DISTRIBUTION_CENTER"
    FASTFOOD_RESTAURANT = "FASTFOOD_RESTAURANT"
    FINANCIAL_OFFICE = "FINANCIAL_OFFICE"
    FIRE_STATION = "FIRE_STATION"
    NON_REFRIGERATED_WAREHOUSE = "NON_REFRIGERATED_WAREHOUSE"
    POLICE_STATION = "POLICE_STATION"
    REFRIGERATED_WAREHOUSE = "REFRIGERATED_WAREHOUSE"
    RETAIL_STORE = "RETAIL_STORE"
    SELF_STORAGE_FACILITY = "SELF_STORAGE_FACILITY"
    SENIOR_CARE_COMMUNITY = "SENIOR_CARE_COMMUNITY"
    SUPERMARKET_GROCERY = "SUPERMARKET_GROCERY"
    RESTAURANT = "RESTAURANT"
    PUBLIC_LIBRARY = "PUBLIC_LIBRARY"
    OTHER = "OTHER"


def space_type_to_benchmark_category(space_type_value: str) -> BenchmarkCategory:
    normalized = normalize_space_type(space_type_value)
    for st in BuildingSpaceType:
        if st.value == normalized:
            if st.name in BenchmarkCategory.__members__:
                return BenchmarkCategory[st.name]
            return BenchmarkCategory.OTHER
    return BenchmarkCategory.OTHER
