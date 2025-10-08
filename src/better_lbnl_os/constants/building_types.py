"""Enum definitions used across the library."""

from enum import Enum


class BuildingSpaceType(Enum):
    """Building space types with both display names and benchmark identifiers."""

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

    @property
    def benchmark_id(self) -> str:
        """Get the benchmark identifier for this building type."""
        return {
            self.OFFICE: "OFFICE",
            self.HOTEL: "HOTEL",
            self.K12: "K12",
            self.MULTIFAMILY_HOUSING: "MULTIFAMILY_HOUSING",
            self.WORSHIP_FACILITY: "WORSHIP_FACILITY",
            self.HOSPITAL: "HOSPITAL",
            self.MUSEUM: "MUSEUM",
            self.BANK_BRANCH: "BANK_BRANCH",
            self.COURTHOUSE: "COURTHOUSE",
            self.DATA_CENTER: "DATA_CENTER",
            self.DISTRIBUTION_CENTER: "DISTRIBUTION_CENTER",
            self.FASTFOOD_RESTAURANT: "FASTFOOD_RESTAURANT",
            self.FINANCIAL_OFFICE: "FINANCIAL_OFFICE",
            self.FIRE_STATION: "FIRE_STATION",
            self.NON_REFRIGERATED_WAREHOUSE: "NON_REFRIGERATED_WAREHOUSE",
            self.POLICE_STATION: "POLICE_STATION",
            self.REFRIGERATED_WAREHOUSE: "REFRIGERATED_WAREHOUSE",
            self.RETAIL_STORE: "RETAIL_STORE",
            self.SELF_STORAGE_FACILITY: "SELF_STORAGE_FACILITY",
            self.SENIOR_CARE_COMMUNITY: "SENIOR_CARE_COMMUNITY",
            self.SUPERMARKET_GROCERY: "SUPERMARKET_GROCERY",
            self.RESTAURANT: "RESTAURANT",
            self.PUBLIC_LIBRARY: "PUBLIC_LIBRARY",
            self.OTHER: "OTHER",
        }[self]

    @classmethod
    def from_benchmark_id(cls, benchmark_id: str) -> "BuildingSpaceType":
        """Get BuildingSpaceType from benchmark identifier."""
        benchmark_map = {
            "OFFICE": cls.OFFICE,
            "HOTEL": cls.HOTEL,
            "K12": cls.K12,
            "MULTIFAMILY_HOUSING": cls.MULTIFAMILY_HOUSING,
            "WORSHIP_FACILITY": cls.WORSHIP_FACILITY,
            "HOSPITAL": cls.HOSPITAL,
            "MUSEUM": cls.MUSEUM,
            "BANK_BRANCH": cls.BANK_BRANCH,
            "COURTHOUSE": cls.COURTHOUSE,
            "DATA_CENTER": cls.DATA_CENTER,
            "DISTRIBUTION_CENTER": cls.DISTRIBUTION_CENTER,
            "FASTFOOD_RESTAURANT": cls.FASTFOOD_RESTAURANT,
            "FINANCIAL_OFFICE": cls.FINANCIAL_OFFICE,
            "FIRE_STATION": cls.FIRE_STATION,
            "NON_REFRIGERATED_WAREHOUSE": cls.NON_REFRIGERATED_WAREHOUSE,
            "POLICE_STATION": cls.POLICE_STATION,
            "REFRIGERATED_WAREHOUSE": cls.REFRIGERATED_WAREHOUSE,
            "RETAIL_STORE": cls.RETAIL_STORE,
            "SELF_STORAGE_FACILITY": cls.SELF_STORAGE_FACILITY,
            "SENIOR_CARE_COMMUNITY": cls.SENIOR_CARE_COMMUNITY,
            "SUPERMARKET_GROCERY": cls.SUPERMARKET_GROCERY,
            "RESTAURANT": cls.RESTAURANT,
            "PUBLIC_LIBRARY": cls.PUBLIC_LIBRARY,
            "OTHER": cls.OTHER,
        }
        if benchmark_id not in benchmark_map:
            raise ValueError(f"Unknown benchmark ID: {benchmark_id}")
        return benchmark_map[benchmark_id]


def space_type_to_benchmark_category(space_type: str) -> BuildingSpaceType:
    """Map a space type string to a BuildingSpaceType enum.

    Args:
        space_type: Building space type as string (e.g., "Office", "OFFICE", "Hotel")

    Returns:
        BuildingSpaceType enum value

    Raises:
        ValueError: If space_type doesn't match any known type

    Examples:
        >>> space_type_to_benchmark_category("Office")
        BuildingSpaceType.OFFICE
        >>> space_type_to_benchmark_category("OFFICE")
        BuildingSpaceType.OFFICE
        >>> space_type_to_benchmark_category("K-12 School")
        BuildingSpaceType.K12
    """
    if not space_type:
        return BuildingSpaceType.OTHER

    # Normalize the input
    normalized = space_type.strip()

    # Try exact match with enum value (display name)
    for building_type in BuildingSpaceType:
        if building_type.value == normalized:
            return building_type

    # Try exact match with enum name
    for building_type in BuildingSpaceType:
        if building_type.name == normalized.upper().replace("-", "_").replace(" ", "_"):
            return building_type

    # Try exact match with benchmark_id
    for building_type in BuildingSpaceType:
        if building_type.benchmark_id == normalized.upper():
            return building_type

    # If no match found, return OTHER
    return BuildingSpaceType.OTHER
