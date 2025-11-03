"""Mappings and normalization helpers."""

from .building_types import BuildingSpaceType

SPACE_TYPE_SYNONYMS: dict[str, str] = {
    "Retail": BuildingSpaceType.RETAIL_STORE.value,
    "School": BuildingSpaceType.K12.value,
    "Warehouse": BuildingSpaceType.NON_REFRIGERATED_WAREHOUSE.value,
    "Library": BuildingSpaceType.PUBLIC_LIBRARY.value,
}


def normalize_space_type(value: str) -> str:
    """Normalize a user-provided space type to a canonical display label."""
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
    raise ValueError(f"Space type must be one of {[st.value for st in BuildingSpaceType]}")


def space_type_to_building_space_type(space_type_value: str) -> BuildingSpaceType:
    """Convert a space type value to BuildingSpaceType enum."""
    normalized = normalize_space_type(space_type_value)
    for st in BuildingSpaceType:
        if st.value == normalized:
            return st
    return BuildingSpaceType.OTHER
