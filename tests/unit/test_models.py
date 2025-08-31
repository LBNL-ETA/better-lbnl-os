"""Unit tests for domain models."""

import pytest
from datetime import date
from better_lbnl.data.models import BuildingData, UtilityBillData


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

    def test_calculate_eui(self):
        """Test EUI calculation."""
        building = BuildingData(
            name="Test Building",
            floor_area=10000,
            space_type="Office",
            location="Berkeley, CA"
        )
        
        # 34,120 kWh * 3.412 kBtu/kWh = 116,441.44 kBtu
        # 116,441.44 kBtu / 10,000 sqft = 11.64 kBtu/sqft/year
        eui = building.calculate_eui(annual_energy_kwh=34120)
        assert abs(eui - 11.641744) < 0.001

    def test_invalid_space_type(self):
        """Test validation of space type."""
        with pytest.raises(ValueError, match="Space type must be one of"):
            BuildingData(
                name="Test",
                floor_area=1000,
                space_type="InvalidType",
                location="Berkeley, CA"
            )

    def test_get_benchmark_category(self):
        """Test benchmark category mapping."""
        building = BuildingData(
            name="Test",
            floor_area=1000,
            space_type="Office",
            location="Berkeley, CA"
        )
        
        assert building.get_benchmark_category() == "COMMERCIAL_OFFICE"


class TestUtilityBillData:
    """Test UtilityBillData domain model."""

    def test_bill_creation(self):
        """Test creating a UtilityBillData instance."""
        bill = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=1000,
            units="kWh",
            cost=150.0
        )
        
        assert bill.fuel_type == "ELECTRICITY"
        assert bill.consumption == 1000
        assert bill.cost == 150.0

    def test_to_kwh_conversion(self):
        """Test energy unit conversion to kWh."""
        # Test electricity (no conversion)
        bill_elec = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=1000,
            units="kWh"
        )
        assert bill_elec.to_kwh() == 1000
        
        # Test natural gas conversion (therms to kWh)
        bill_gas = UtilityBillData(
            fuel_type="NATURAL_GAS",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=100,
            units="therms"
        )
        assert bill_gas.to_kwh() == 2930  # 100 therms * 29.3 kWh/therm

    def test_get_days(self):
        """Test billing period day calculation."""
        bill = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=1000,
            units="kWh"
        )
        
        assert bill.get_days() == 30

    def test_invalid_dates(self):
        """Test date validation."""
        with pytest.raises(ValueError, match="End date must be after start date"):
            UtilityBillData(
                fuel_type="ELECTRICITY",
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1),
                consumption=1000,
                units="kWh"
            )