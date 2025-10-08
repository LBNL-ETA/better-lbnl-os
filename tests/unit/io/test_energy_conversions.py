from datetime import date

import pytest

from better_lbnl_os.constants.energy import (
    FuelType,
    FuelUnit,
    get_conversion_factor,
    normalize_fuel_type,
    normalize_fuel_unit,
)
from better_lbnl_os.core.preprocessing import calendarize_utility_bills
from better_lbnl_os.models import UtilityBillData
from better_lbnl_os.models.utility_bills import CalendarizedData


def test_normalize_fuel_type_aliases():
    assert normalize_fuel_type("Electric - Grid") == FuelType.ELECTRIC_GRID.value
    assert normalize_fuel_type("Fuel Oil (No. 4)") == FuelType.FUEL_OIL_4.value
    assert normalize_fuel_type("Agua caliente de distrito") == FuelType.DISTRICT_HOT_WATER.value


def test_normalize_fuel_unit_aliases():
    assert normalize_fuel_unit("kWh") == FuelUnit.KWH.value
    assert normalize_fuel_unit("Gallons (US)") == FuelUnit.GALLONS_US.value
    assert normalize_fuel_unit("ton hours") == FuelUnit.TON_HOURS.value


def test_get_conversion_factor_matches_expected():
    factor = get_conversion_factor("Fuel Oil (No. 4)", "Gallons (US)")
    assert factor is not None
    assert factor == pytest.approx(42.788, rel=1e-6)


def test_calendarization_converts_complex_units():
    bills = [
        UtilityBillData(
            fuel_type="Fuel Oil (No. 4)",
            units="Gallons (US)",
            consumption=10.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            cost=None,
        )
    ]
    calendarized = calendarize_utility_bills(bills=bills, floor_area=100.0)
    # calendarize_utility_bills now returns CalendarizedData model
    assert isinstance(calendarized, CalendarizedData)
    energy_dict = calendarized.detailed.energy_kwh
    # The key format is the fuel type
    key = "FUEL_OIL_4"
    assert key in energy_dict
    assert energy_dict[key][0] == pytest.approx(427.88, rel=1e-6)
