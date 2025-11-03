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
            climate_zone="3C",
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
                name="Test", floor_area=1000, space_type="InvalidType", location="Berkeley, CA"
            )

    # @pytest.mark.skip(reason="space_type_to_benchmark_category function not implemented")
    def test_get_benchmark_category(self):
        """Test benchmark category mapping."""
        building = BuildingData(
            name="Test", floor_area=1000, space_type="Office", location="Berkeley, CA"
        )

        # With one-to-one mapping, Office maps to OFFICE
        assert building.get_benchmark_category() == "OFFICE"

    def test_get_space_type_code(self):
        """Test space type code retrieval."""
        building = BuildingData(
            name="Test", floor_area=1000, space_type="Office", location="Berkeley, CA"
        )
        assert building.get_space_type_code() == "OFFICE"

        # Test another space type
        building2 = BuildingData(
            name="Test Hotel", floor_area=2000, space_type="Hotel", location="San Francisco, CA"
        )
        assert building2.get_space_type_code() == "HOTEL"

    def test_validate_bills_empty(self):
        """Test validation with no bills."""

        building = BuildingData(
            name="Test", floor_area=1000, space_type="Office", location="Berkeley, CA"
        )

        errors = building.validate_bills([])
        assert len(errors) == 1
        assert "No utility bills provided" in errors[0]

    def test_validate_bills_with_gaps(self):
        """Test validation detects gaps between billing periods."""
        from datetime import date

        from better_lbnl_os.models import UtilityBillData

        building = BuildingData(
            name="Test", floor_area=1000, space_type="Office", location="Berkeley, CA"
        )

        bills = [
            UtilityBillData(
                fuel_type="ELECTRICITY",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                consumption=1000,
                units="kWh",
            ),
            UtilityBillData(
                fuel_type="ELECTRICITY",
                start_date=date(2024, 2, 5),  # 5-day gap
                end_date=date(2024, 2, 28),
                consumption=1100,
                units="kWh",
            ),
        ]

        errors = building.validate_bills(bills)
        assert len(errors) >= 1
        assert any("Gap of" in err and "days" in err for err in errors)

    def test_validate_bills_non_positive_consumption(self):
        """Test validation detects non-positive consumption."""
        from datetime import date

        from better_lbnl_os.models import UtilityBillData

        building = BuildingData(
            name="Test", floor_area=1000, space_type="Office", location="Berkeley, CA"
        )

        bills = [
            UtilityBillData(
                fuel_type="ELECTRICITY",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                consumption=0,  # Zero consumption
                units="kWh",
            )
        ]

        errors = building.validate_bills(bills)
        assert len(errors) >= 1
        assert any("Non-positive consumption" in err for err in errors)

    def test_validate_bills_unusually_high_consumption(self):
        """Test validation detects unusually high consumption."""
        from datetime import date

        from better_lbnl_os.models import UtilityBillData

        building = BuildingData(
            name="Test", floor_area=1000, space_type="Office", location="Berkeley, CA"
        )

        bills = [
            UtilityBillData(
                fuel_type="ELECTRICITY",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                consumption=50000000,  # Extremely high consumption
                units="kWh",
            )
        ]

        errors = building.validate_bills(bills)
        assert len(errors) >= 1
        assert any("Unusually high consumption" in err for err in errors)

    def test_validate_bills_valid(self):
        """Test validation passes with valid bills."""
        from datetime import date

        from better_lbnl_os.models import UtilityBillData

        building = BuildingData(
            name="Test", floor_area=1000, space_type="Office", location="Berkeley, CA"
        )

        bills = [
            UtilityBillData(
                fuel_type="ELECTRICITY",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                consumption=1000,
                units="kWh",
            ),
            UtilityBillData(
                fuel_type="ELECTRICITY",
                start_date=date(2024, 1, 31),
                end_date=date(2024, 2, 29),
                consumption=1100,
                units="kWh",
            ),
        ]

        errors = building.validate_bills(bills)
        assert len(errors) == 0
