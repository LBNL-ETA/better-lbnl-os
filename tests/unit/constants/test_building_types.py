"""Unit tests for BuildingSpaceType enum and related functions."""

import pytest

from better_lbnl_os.constants.building_types import (
    BuildingSpaceType,
    space_type_to_benchmark_category,
)


class TestBuildingSpaceType:
    """Test BuildingSpaceType enum."""

    def test_benchmark_id_property(self):
        """Test that benchmark_id property returns correct values."""
        assert BuildingSpaceType.OFFICE.benchmark_id == "OFFICE"
        assert BuildingSpaceType.HOTEL.benchmark_id == "HOTEL"
        assert BuildingSpaceType.K12.benchmark_id == "K12"
        assert BuildingSpaceType.MULTIFAMILY_HOUSING.benchmark_id == "MULTIFAMILY_HOUSING"
        assert BuildingSpaceType.HOSPITAL.benchmark_id == "HOSPITAL"
        assert BuildingSpaceType.RETAIL_STORE.benchmark_id == "RETAIL_STORE"
        assert BuildingSpaceType.OTHER.benchmark_id == "OTHER"

    def test_benchmark_id_all_types(self):
        """Test benchmark_id for all building types."""
        # Ensure all enum members have a benchmark_id
        for building_type in BuildingSpaceType:
            assert isinstance(building_type.benchmark_id, str)
            assert len(building_type.benchmark_id) > 0

    def test_from_benchmark_id_valid(self):
        """Test from_benchmark_id with valid IDs."""
        assert BuildingSpaceType.from_benchmark_id("OFFICE") == BuildingSpaceType.OFFICE
        assert BuildingSpaceType.from_benchmark_id("HOTEL") == BuildingSpaceType.HOTEL
        assert BuildingSpaceType.from_benchmark_id("K12") == BuildingSpaceType.K12
        assert (
            BuildingSpaceType.from_benchmark_id("MULTIFAMILY_HOUSING")
            == BuildingSpaceType.MULTIFAMILY_HOUSING
        )
        assert BuildingSpaceType.from_benchmark_id("HOSPITAL") == BuildingSpaceType.HOSPITAL
        assert BuildingSpaceType.from_benchmark_id("MUSEUM") == BuildingSpaceType.MUSEUM
        assert BuildingSpaceType.from_benchmark_id("BANK_BRANCH") == BuildingSpaceType.BANK_BRANCH
        assert BuildingSpaceType.from_benchmark_id("DATA_CENTER") == BuildingSpaceType.DATA_CENTER
        assert BuildingSpaceType.from_benchmark_id("RETAIL_STORE") == BuildingSpaceType.RETAIL_STORE
        assert BuildingSpaceType.from_benchmark_id("OTHER") == BuildingSpaceType.OTHER

    def test_from_benchmark_id_invalid(self):
        """Test from_benchmark_id raises ValueError for invalid ID."""
        with pytest.raises(ValueError, match="Unknown benchmark ID: INVALID_TYPE"):
            BuildingSpaceType.from_benchmark_id("INVALID_TYPE")

        with pytest.raises(ValueError, match="Unknown benchmark ID: "):
            BuildingSpaceType.from_benchmark_id("")

    def test_enum_values(self):
        """Test that enum values are display names."""
        assert BuildingSpaceType.OFFICE.value == "Office"
        assert BuildingSpaceType.K12.value == "K-12 School"
        assert BuildingSpaceType.MULTIFAMILY_HOUSING.value == "Multifamily Housing"


class TestSpaceTypeToBenchmarkCategory:
    """Test space_type_to_benchmark_category function."""

    def test_empty_string_returns_other(self):
        """Test empty string returns OTHER."""
        assert space_type_to_benchmark_category("") == BuildingSpaceType.OTHER
        assert space_type_to_benchmark_category("   ") == BuildingSpaceType.OTHER

    def test_none_returns_other(self):
        """Test None/falsy values return OTHER."""
        assert space_type_to_benchmark_category(None) == BuildingSpaceType.OTHER

    def test_display_name_matching(self):
        """Test exact match with display names."""
        assert space_type_to_benchmark_category("Office") == BuildingSpaceType.OFFICE
        assert space_type_to_benchmark_category("Hotel") == BuildingSpaceType.HOTEL
        assert space_type_to_benchmark_category("K-12 School") == BuildingSpaceType.K12
        assert (
            space_type_to_benchmark_category("Multifamily Housing")
            == BuildingSpaceType.MULTIFAMILY_HOUSING
        )
        assert (
            space_type_to_benchmark_category("Hospital (General Medical & Surgical)")
            == BuildingSpaceType.HOSPITAL
        )
        assert space_type_to_benchmark_category("Retail Store") == BuildingSpaceType.RETAIL_STORE
        assert space_type_to_benchmark_category("Other") == BuildingSpaceType.OTHER

    def test_enum_name_matching(self):
        """Test matching with enum names."""
        assert space_type_to_benchmark_category("OFFICE") == BuildingSpaceType.OFFICE
        assert space_type_to_benchmark_category("HOTEL") == BuildingSpaceType.HOTEL
        assert space_type_to_benchmark_category("K12") == BuildingSpaceType.K12
        assert (
            space_type_to_benchmark_category("MULTIFAMILY_HOUSING")
            == BuildingSpaceType.MULTIFAMILY_HOUSING
        )
        assert space_type_to_benchmark_category("RETAIL_STORE") == BuildingSpaceType.RETAIL_STORE

    def test_benchmark_id_matching(self):
        """Test matching with benchmark IDs (same as enum names in this case)."""
        assert space_type_to_benchmark_category("OFFICE") == BuildingSpaceType.OFFICE
        assert space_type_to_benchmark_category("K12") == BuildingSpaceType.K12
        assert space_type_to_benchmark_category("DATA_CENTER") == BuildingSpaceType.DATA_CENTER

    def test_whitespace_normalization(self):
        """Test that whitespace is trimmed."""
        assert space_type_to_benchmark_category("  Office  ") == BuildingSpaceType.OFFICE
        assert space_type_to_benchmark_category("\tHotel\n") == BuildingSpaceType.HOTEL

    def test_unknown_type_returns_other(self):
        """Test unknown types return OTHER."""
        assert space_type_to_benchmark_category("Unknown Building Type") == BuildingSpaceType.OTHER
        assert space_type_to_benchmark_category("InvalidType") == BuildingSpaceType.OTHER
        assert space_type_to_benchmark_category("random") == BuildingSpaceType.OTHER

    def test_all_display_names_work(self):
        """Test all enum display names are recognized."""
        for building_type in BuildingSpaceType:
            result = space_type_to_benchmark_category(building_type.value)
            assert result == building_type

    def test_all_enum_names_work(self):
        """Test all enum names are recognized."""
        for building_type in BuildingSpaceType:
            result = space_type_to_benchmark_category(building_type.name)
            assert result == building_type

    def test_all_benchmark_ids_work(self):
        """Test all benchmark IDs are recognized."""
        for building_type in BuildingSpaceType:
            result = space_type_to_benchmark_category(building_type.benchmark_id)
            assert result == building_type
