"""Unit tests for UtilityBillData domain model."""

import pytest
from datetime import date
from better_lbnl_os.models import UtilityBillData


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
        assert abs(bill_gas.to_kwh() - 2930.7) < 0.1  # 100 therms * 29.307 kWh/therm

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
