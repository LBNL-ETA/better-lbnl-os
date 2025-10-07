"""Tests for preprocessing calendarization of utility bills."""

from datetime import date

from better_lbnl_os.core.preprocessing import (
    calendarize_utility_bills,
    CalendarizationOptions,
)
from better_lbnl_os.models import UtilityBillData, WeatherData


def test_calendarize_basic_electricity_only():
    bills = [
        UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            consumption=30000,
            units="kWh",
            cost=4500.0,
        ),
        UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2023, 2, 1),
            end_date=date(2023, 2, 28),
            consumption=28000,
            units="kWh",
            cost=4200.0,
        ),
    ]

    weather = [
        WeatherData(latitude=0.0, longitude=0.0, year=2023, month=1, avg_temp_c=10.0),
        WeatherData(latitude=0.0, longitude=0.0, year=2023, month=2, avg_temp_c=12.0),
    ]

    res = calendarize_utility_bills(bills, floor_area=10000.0, weather=weather)

    # Validate keys
    assert set(res.keys()) == {"weather", "detailed", "aggregated"}

    # Two months
    assert len(res["aggregated"]["periods"]) == 2
    assert len(res["aggregated"]["days_in_period"]) == 2

    # Energy totals by Energy_Type
    energy = res["aggregated"]["dict_v_energy"]["ELECTRICITY"]
    assert energy[0] == 30000
    assert energy[1] == 28000

    # Unit price equals cost/kwh
    unit_prices = res["aggregated"]["dict_v_unit_prices"]["ELECTRICITY"]
    assert round(unit_prices[0], 6) == round(4500.0 / 30000.0, 6)
    assert round(unit_prices[1], 6) == round(4200.0 / 28000.0, 6)

    # Daily EUI present
    eui = res["aggregated"]["dict_v_eui"]["ELECTRICITY"]
    # Jan: 30000 / 10000 / 31
    assert round(eui[0], 6) == round(30000 / 10000.0 / 31.0, 6)

    # Weather merged
    assert res["weather"]["degC"] == [10.0, 12.0]


def test_calendarize_with_gas_conversion_and_emissions():
    bills = [
        UtilityBillData(
            fuel_type="NATURAL_GAS",
            start_date=date(2023, 3, 1),
            end_date=date(2023, 3, 31),
            consumption=1000,
            units="therms",
            cost=1000.0,
        ),
    ]

    # Provide emission factor and energy type map (optional)
    opts = CalendarizationOptions(
        energy_type_map={"NATURAL_GAS": "FOSSIL_FUEL"},
        emission_factor_by_fuel={"NATURAL_GAS": 0.18},
    )
    res = calendarize_utility_bills(bills, floor_area=5000.0, weather=None, options=opts)

    # Should have one month
    assert res["aggregated"]["periods"][0].startswith("2023-03-01")

    # Converted to kWh: 1000 therms * 29.3
    energy = res["aggregated"]["dict_v_energy"]["FOSSIL_FUEL"][0]
    assert round(energy, 2) == round(1000 * 29.3, 2)

    # Emissions present (kg CO2): kWh * factor
    ghg = res["aggregated"]["dict_v_ghg"]["FOSSIL_FUEL"][0]
    assert round(ghg, 2) == round(1000 * 29.3 * 0.18, 2)
