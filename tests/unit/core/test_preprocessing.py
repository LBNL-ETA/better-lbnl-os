"""Tests for preprocessing calendarization of utility bills."""

import math
from datetime import date

from better_lbnl_os.core.preprocessing import (
    CalendarizationOptions,
    calendarize_utility_bills,
)
from better_lbnl_os.models import UtilityBillData, WeatherData
from better_lbnl_os.models.utility_bills import CalendarizedData


def _assert_all_finite(values: list[float]) -> None:
    assert all(math.isfinite(v) for v in values)


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

    # Now returns CalendarizedData model instead of dict
    assert isinstance(res, CalendarizedData)

    # Two months
    assert len(res.aggregated.months) == 2
    assert len(res.aggregated.days_in_period) == 2

    # Energy totals by Energy_Type
    energy = res.aggregated.energy_kwh["ELECTRICITY"]
    assert energy[0] == 30000
    assert energy[1] == 28000

    # Unit price equals cost/kwh
    unit_prices = res.aggregated.unit_price_per_kwh["ELECTRICITY"]
    assert round(unit_prices[0], 6) == round(4500.0 / 30000.0, 6)
    assert round(unit_prices[1], 6) == round(4200.0 / 28000.0, 6)

    # Daily EUI present
    eui = res.aggregated.daily_eui_kwh_per_m2["ELECTRICITY"]
    # Jan: 30000 / 10000 / 31
    assert round(eui[0], 6) == round(30000 / 10000.0 / 31.0, 6)

    # Weather merged
    assert res.weather.degC == [10.0, 12.0]


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

    # Now returns CalendarizedData model
    assert isinstance(res, CalendarizedData)

    # Should have one month
    assert res.aggregated.months[0].strftime("%Y-%m-%d") == "2023-03-01"

    # Converted to kWh: 1000 therms * 29.307 (actual conversion factor)
    energy = res.aggregated.energy_kwh["FOSSIL_FUEL"][0]
    assert round(energy, 2) == round(1000 * 29.307, 2)

    # Emissions present (kg CO2): kWh * factor
    ghg = res.aggregated.ghg_kg["FOSSIL_FUEL"][0]
    assert round(ghg, 2) == round(1000 * 29.307 * 0.18, 2)


def test_calendarize_zero_consumption_with_cost_does_not_emit_infinity():
    """Regression for LBNL-ETA/better_lbnl#559: cost ÷ 0 consumption must not yield Inf."""
    bills = [
        UtilityBillData(
            fuel_type="NATURAL_GAS",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 31),
            consumption=1000,
            units="therms",
            cost=800.0,
        ),
        UtilityBillData(
            fuel_type="NATURAL_GAS",
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 31),
            consumption=0,
            units="therms",
            cost=50.0,
        ),
    ]
    opts = CalendarizationOptions(
        energy_type_map={"NATURAL_GAS": "FOSSIL_FUEL"},
        emission_factor_by_fuel={"NATURAL_GAS": 0.18},
    )
    res = calendarize_utility_bills(bills, floor_area=5000.0, weather=None, options=opts)

    assert isinstance(res, CalendarizedData)
    assert len(res.aggregated.months) == 2

    for prices in res.aggregated.unit_price_per_kwh.values():
        _assert_all_finite(prices)
    for prices in res.detailed.unit_price_per_kwh.values():
        _assert_all_finite(prices)
    for factors in res.aggregated.unit_emission_kg_per_kwh.values():
        _assert_all_finite(factors)
    for factors in res.detailed.unit_emission_kg_per_kwh.values():
        _assert_all_finite(factors)

    # Zero-consumption August is filled from the July mean unit price (fill_strategy=mean).
    july_price = res.aggregated.unit_price_per_kwh["FOSSIL_FUEL"][0]
    august_price = res.aggregated.unit_price_per_kwh["FOSSIL_FUEL"][1]
    assert round(july_price, 6) == round(800.0 / (1000 * 29.307), 6)
    assert round(august_price, 6) == round(july_price, 6)

    legacy = res.to_legacy_dict()
    for prices in legacy["aggregated"]["dict_v_unit_prices"].values():
        _assert_all_finite(prices)
    for prices in legacy["detailed"]["dict_v_unit_prices"].values():
        _assert_all_finite(prices)
