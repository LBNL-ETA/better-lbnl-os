"""Unit tests for BuildingData domain model."""

import pytest
from better_lbnl_os.models import BuildingData


class TestBuildingData:
    """Test BuildingData domain model."""

    def test_building_creation(self):
        """Test creating a BuildingData instance."""
        building = BuildingData(
            name="Test Office",
            floor_area=50000,
            space_type="Office",
            location="Berkeley, CA",
            country_code="US",
            climate_zone="3C"
        )

        assert building.name == "Test Office"
        assert building.floor_area == 50000
        assert building.space_type == "Office"
        assert building.location == "Berkeley, CA"

    # EUI calculations are handled by services/algorithms in OS library

    def test_invalid_space_type(self):
        """Test validation of space type."""
        with pytest.raises(ValueError, match="Space type must be one of"):
            BuildingData(
                name="Test",
                floor_area=1000,
                space_type="InvalidType",
                location="Berkeley, CA"
            )

    @pytest.mark.skip(reason="space_type_to_benchmark_category function not implemented")
    def test_get_benchmark_category(self):
        """Test benchmark category mapping."""
        building = BuildingData(
            name="Test",
            floor_area=1000,
            space_type="Office",
            location="Berkeley, CA"
        )

        # With one-to-one mapping, Office maps to OFFICE
        assert building.get_benchmark_category() == "OFFICE"
