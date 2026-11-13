"""Tests for preprocessing calendarization of utility bills."""

import json
import math
from datetime import date

import pytest

from better_lbnl_os.core.preprocessing import (
    CalendarizationOptions,
    calendarize_utility_bills,
)
from better_lbnl_os.core.savings import estimate_savings_for_fuel
from better_lbnl_os.models import LocationSummary, UtilityBillData, WeatherData
from better_lbnl_os.models.utility_bills import CalendarizedData


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


def test_calendarize_zero_consumption_with_cost_imputes_finite_mean():
    """Zero-consumption standing-charge month must not emit Infinity or poison mean fill."""
    bills = [
        # Electricity in Jan, Feb, Mar so all three calendar months exist
        UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            consumption=10000,
            units="kWh",
            cost=1500.0,
        ),
        UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            consumption=9000,
            units="kWh",
            cost=1350.0,
        ),
        UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            consumption=9500,
            units="kWh",
            cost=1425.0,
        ),
        # Natural gas: positive usage in Jan, zero usage + standing charge in Feb, no bill in Mar
        UtilityBillData(
            fuel_type="NATURAL_GAS",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            consumption=100,
            units="therms",
            cost=120.0,
        ),
        UtilityBillData(
            fuel_type="NATURAL_GAS",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            consumption=0,
            units="therms",
            cost=50.0,
        ),
    ]
    opts = CalendarizationOptions(
        energy_type_map={"ELECTRICITY": "ELECTRICITY", "NATURAL_GAS": "FOSSIL_FUEL"},
        emission_factor_by_fuel={"NATURAL_GAS": 0.18},
    )

    res = calendarize_utility_bills(bills, floor_area=5000.0, options=opts)
    legacy = res.to_legacy_dict()

    # Strict JSON serialization (rejects NaN / Infinity / -Infinity just like PostgreSQL jsonb)
    encoded = json.dumps(legacy, allow_nan=False)
    assert "Infinity" not in encoded
    assert "NaN" not in encoded

    # Standing charge in Feb is still recorded in total costs while consumption is 0
    assert res.aggregated.cost["FOSSIL_FUEL"] == pytest.approx([120.0, 50.0, 0.0])
    assert res.aggregated.energy_kwh["FOSSIL_FUEL"] == pytest.approx([100 * 29.307, 0.0, 0.0])

    # Unit price for Feb (0 consumption) and Mar (missing gas bill) is imputed from Jan's finite rate
    expected_rate = 120.0 / (100 * 29.307)
    assert res.aggregated.unit_price_per_kwh["FOSSIL_FUEL"] == pytest.approx(
        [expected_rate, expected_rate, expected_rate]
    )
    assert res.detailed.unit_price_per_kwh["NATURAL_GAS"] == pytest.approx(
        [expected_rate, expected_rate, expected_rate]
    )
    assert res.aggregated.unit_emission_kg_per_kwh["FOSSIL_FUEL"] == pytest.approx(
        [0.18, 0.18, 0.18]
    )


def test_calendarize_only_zero_consumption_bills_defaults_rates_to_zero():
    """When every month has zero consumption and positive cost, unit rates fall back to 0.0."""
    bills = [
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

    res = calendarize_utility_bills(bills, floor_area=5000.0, options=opts)
    legacy = res.to_legacy_dict()
    json.dumps(legacy, allow_nan=False)

    assert res.aggregated.cost["FOSSIL_FUEL"] == pytest.approx([50.0])
    assert res.aggregated.unit_price_per_kwh["FOSSIL_FUEL"] == [0.0]
    assert res.detailed.unit_price_per_kwh["NATURAL_GAS"] == [0.0]
    assert res.aggregated.unit_emission_kg_per_kwh["FOSSIL_FUEL"] == [0.0]


def test_estimate_savings_handles_none_and_nonfinite_unit_rates_in_legacy_dict():
    """Legacy dicts containing None or ±Inf in unit rates must fall back cleanly, not crash."""
    months_13 = [f"2024-{m:02d}-01" for m in range(1, 13)] + ["2025-01-01"]
    legacy = {
        "weather": {"degC": [5.0 + m for m in range(13)], "degF": [41.0 + m for m in range(13)]},
        "aggregated": {
            "periods": months_13,
            "v_x": months_13,
            "days_in_period": [30] * 13,
            "ls_n_days": [30] * 13,
            # Month 1 has 0 EUI (outside trailing 12 positive months) with None/Inf rates;
            # Month 2 (inside window) also has None/Inf rates to exercise _fill_unit_prices fallback.
            "dict_v_eui": {"FOSSIL_FUEL": [0.0] + [0.5] * 12},
            "dict_v_energy": {"FOSSIL_FUEL": [0.0] + [15000.0] * 12},
            "dict_v_costs": {"FOSSIL_FUEL": [50.0] + [600.0] * 12},
            "dict_v_ghg": {"FOSSIL_FUEL": [0.0] + [2700.0] * 12},
            "dict_v_unit_prices": {"FOSSIL_FUEL": [None, float("inf")] + [0.04] * 11},
            "dict_v_ghg_factors": {"FOSSIL_FUEL": [float("-inf"), float("nan")] + [0.18] * 11},
        },
        "detailed": {},
    }
    benchmark_data = {
        "FOSSIL_FUEL": {
            "baseload": {"coefficient_value": 0.4, "target_value": 0.3, "nominal_level": 0.35},
            "heating_slope": {
                "coefficient_value": -0.02,
                "target_value": -0.015,
                "nominal_level": -0.018,
            },
            "heating_change_point": {
                "coefficient_value": 15.0,
                "target_value": 14.0,
                "nominal_level": 14.5,
            },
            "cooling_change_point": {
                "coefficient_value": None,
                "target_value": None,
                "nominal_level": None,
            },
            "cooling_slope": {
                "coefficient_value": None,
                "target_value": None,
                "nominal_level": None,
            },
        }
    }

    res = estimate_savings_for_fuel(
        benchmark_data=benchmark_data,
        calendarized=legacy,
        floor_area=1000.0,
        energy_type="FOSSIL_FUEL",
        location_context=LocationSummary(country_code="US", state_code="CA"),
    )
    assert math.isfinite(res.cost_savings_usd)
    assert math.isfinite(res.ghg_savings_kg_co2)
    assert res.cost_savings_usd > 0
