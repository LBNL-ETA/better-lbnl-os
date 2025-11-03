"""End-to-end integration test for the complete BETTER workflow.

This test validates the entire workflow from calendarized utility bills through
change-point modeling, benchmarking, recommendations, and savings estimation.

Test data includes office buildings from multiple climates:
- Miami, FL: Warm climate with both electricity and fossil fuel
- Houston, TX: Hot/humid climate with electricity only (no fossil fuel model)

Results are validated against known Django app outputs to ensure backward compatibility.
"""

import json
from pathlib import Path

import pytest

from better_lbnl_os import (
    benchmark_with_reference,
    estimate_savings,
    fit_calendarized_models,
    recommend_ee_measures,
)
from better_lbnl_os.constants.building_types import BuildingSpaceType
from better_lbnl_os.models import CalendarizedData

# Building configurations - acts as a simple data factory for test parameterization
BUILDING_CONFIGS = {
    "miami": {
        "fixture": "legacy_miami_office_calendarized.json",
        "location": "Miami, FL",
        "floor_area": 4982.19,
        "building_type": BuildingSpaceType.OFFICE,
        "country_code": "US",
        "has_fossil_fuel": True,
        "expected": {
            "electricity": {
                "baseload_coefficient": 0.4067543890878484,
                "cooling_change_point": 24.361560981830078,
                "cooling_slope": 0.014652654315350037,
                "baseload_rating": "Typical",
                "baseload_percentile": 18.6,
                "cooling_change_point_rating": "Good",
                "cooling_change_point_percentile": 99.5,
                "cooling_slope_rating": "Typical",
                "cooling_slope_percentile": 29.0,
                "baseload_cost_savings": 28479.29,
                "cooling_cost_savings": 1778.71,
                "energy_savings_percent": 30.37,
            },
            "fossil_fuel": {
                "heating_slope": -0.0001038106737245206,
                "heating_change_point": 28.500625,
                "baseload_coefficient": 0.0032963292723541533,
                "heating_slope_rating": "Good",
                "heating_slope_percentile": 90.8,
                "heating_change_point_rating": "Poor",
                "heating_change_point_percentile": 0.1,
                "baseload_rating": "Typical",
                "baseload_percentile": 77.8,
                "heating_cost_savings": 25.27,
                "energy_savings_percent": 8.29,
            },
            "combined": {
                "energy_savings_kwh": 242412.27,
                "energy_savings_percent": 30.19,
            },
            "recommendations": {
                "expected_count": 7,  # Exact count from Django HTML
                "expected_measures": [
                    "DECREASE_HEATING_SETPOINTS",  # Poor heating change point
                    "REDUCE_EQUIPMENT_SCHEDULES",  # High baseload
                    "ENSURE_ADEQUATE_VENTILATION_RATE",  # High cooling + heating issues
                    "REDUCE_LIGHTING_LOAD",  # High electricity baseload
                    "REDUCE_PLUG_LOADS",  # High electricity baseload
                    "INCREASE_COOLING_SYSTEM_EFFICIENCY",  # Cooling sensitivity
                    "UPGRADE_WINDOWS_TO_REDUCE_SOLAR_HEAT_GAIN",  # Cooling load
                ],
            },
        },
    },
    "houston": {
        "fixture": "legacy_houston_office_calendarized.json",
        "location": "Houston, TX",
        "floor_area": 4982.19,
        "building_type": BuildingSpaceType.OFFICE,
        "country_code": "US",
        "has_fossil_fuel": False,  # KEY DIFFERENCE: No fossil fuel model
        "expected": {
            "electricity": {
                # Values from HTML (portfolio_building_analytics_ID_155253.html)
                "baseload_coefficient": 0.399,  # 0.399 kWh/(m²·day)
                "baseload_rating": "Typical",
                "baseload_percentile": 20,
                "cooling_change_point": 22.4,  # 22.4°C from HTML
                "cooling_change_point_rating": "Good",
                "cooling_change_point_percentile": 98,
                "cooling_slope": 0.062,  # 62 kWh/°C ÷ 4982.19 m² ≈ 0.0124 kWh/(m²·°C)
                "cooling_slope_rating": "Typical",
                "cooling_slope_percentile": 41,
                "baseload_cost_savings": 21629.88,  # From HTML sunburst
                "cooling_cost_savings": 625.44,  # From HTML sunburst
                "energy_savings_kwh": 219048,  # From HTML table
                "energy_savings_percent": 28.2,  # From HTML table
            },
            "fossil_fuel": None,  # No fossil fuel data for Houston
            "combined": {
                "energy_savings_kwh": 219048,  # Same as electricity (only fuel)
                "energy_savings_percent": 28.2,
            },
            "recommendations": {
                "expected_count": 5,  # Exact count from Django HTML
                "expected_measures": [
                    "REDUCE_EQUIPMENT_SCHEDULES",  # High baseload
                    "REDUCE_LIGHTING_LOAD",  # High electricity baseload
                    "REDUCE_PLUG_LOADS",  # High electricity baseload
                    "INCREASE_COOLING_SYSTEM_EFFICIENCY",  # Cooling load
                    "UPGRADE_WINDOWS_TO_REDUCE_SOLAR_HEAT_GAIN",  # Cooling load
                ],
            },
        },
    },
}


class TestCompleteWorkflow:
    """Integration tests for complete BETTER workflow.

    Tests validate the entire workflow from calendarized utility bills through
    change-point modeling, benchmarking, recommendations, and savings estimation.

    Uses pytest parameterization to test multiple building scenarios with the same logic.
    """

    @pytest.fixture(params=["miami", "houston"])
    def building_config(self, request):
        """Provide building configuration for parameterized tests."""
        return BUILDING_CONFIGS[request.param]

    @pytest.fixture
    def calendarized_data(self, building_config):
        """Load calendarized data for the configured building."""
        fixture_path = (
            Path(__file__).parent.parent / "fixtures" / "utility_bills" / building_config["fixture"]
        )

        with open(fixture_path) as f:
            legacy_dict = json.load(f)

        return CalendarizedData.from_legacy_dict(legacy_dict)

    @pytest.fixture
    def changepoint_results(self, calendarized_data):
        """Fit change-point models."""
        return fit_calendarized_models(calendarized_data)

    @pytest.fixture
    def benchmark_results(self, building_config, changepoint_results):
        """Generate benchmark results."""
        return benchmark_with_reference(
            change_point_results=changepoint_results,
            floor_area=building_config["floor_area"],
            country_code=building_config["country_code"],
            building_type=building_config["building_type"],
        )

    @pytest.fixture
    def recommendations(self, building_config, benchmark_results):
        """Generate EE measure recommendations."""
        return recommend_ee_measures(
            benchmark_results, building_type=building_config["building_type"]
        )

    @pytest.fixture
    def savings(self, building_config, benchmark_results, calendarized_data):
        """Estimate energy and cost savings."""
        return estimate_savings(
            benchmark_results,
            calendarized_data,
            floor_area=building_config["floor_area"],
            savings_target=benchmark_results.savings_target,
        )

    def test_01_load_calendarized_data(self, building_config, calendarized_data):
        """Test loading and converting legacy calendarized data."""
        # Verify basic structure
        assert calendarized_data.weather is not None
        assert calendarized_data.aggregated is not None
        assert calendarized_data.detailed is not None

        # Verify 12 months of data
        assert len(calendarized_data.aggregated.months) == 12
        assert len(calendarized_data.weather.degC) == 12

        # Verify energy types
        energy_types = list(calendarized_data.aggregated.energy_kwh.keys())
        assert "ELECTRICITY" in energy_types

        # Conditionally check for fossil fuel based on building
        if building_config["has_fossil_fuel"]:
            assert "FOSSIL_FUEL" in energy_types or "NATURAL_GAS" in energy_types

    def test_02_fit_changepoint_models(self, building_config, changepoint_results):
        """Test change-point model fitting."""
        # Electricity model should always be present
        assert "ELECTRICITY" in changepoint_results

        # Validate ELECTRICITY model coefficients
        elec_model = changepoint_results["ELECTRICITY"]
        expected = building_config["expected"]["electricity"]

        assert elec_model.baseload == pytest.approx(
            expected["baseload_coefficient"], rel=0.05  # Allow 5% tolerance
        )

        if expected.get("cooling_change_point"):
            assert elec_model.cooling_change_point == pytest.approx(
                expected["cooling_change_point"], abs=2.0  # Allow 2°C tolerance
            )

        # Conditionally validate FOSSIL_FUEL model
        if building_config["has_fossil_fuel"]:
            assert "FOSSIL_FUEL" in changepoint_results
            fossil_model = changepoint_results["FOSSIL_FUEL"]
            ff_expected = building_config["expected"]["fossil_fuel"]

            assert fossil_model.heating_slope == pytest.approx(
                ff_expected["heating_slope"], rel=0.05
            )
            assert fossil_model.heating_change_point == pytest.approx(
                ff_expected["heating_change_point"], rel=0.05
            )
            assert fossil_model.baseload == pytest.approx(
                ff_expected["baseload_coefficient"], rel=0.05
            )
        else:
            # Houston: Either no fossil fuel model or minimal usage
            # The model might exist but not be reliable
            pass

    def test_03_benchmark_results(self, building_config, benchmark_results):
        """Test benchmarking against reference statistics."""
        # Validate ELECTRICITY benchmarks
        elec = benchmark_results.ELECTRICITY
        expected = building_config["expected"]["electricity"]

        assert elec.baseload.rating == expected["baseload_rating"]
        assert elec.baseload.percentile == pytest.approx(
            expected["baseload_percentile"], abs=2.0  # Allow 2 percentile point tolerance
        )

        if "cooling_change_point_rating" in expected:
            assert elec.cooling_change_point.rating == expected["cooling_change_point_rating"]
            assert elec.cooling_change_point.percentile == pytest.approx(
                expected["cooling_change_point_percentile"], abs=2.0
            )

        if "cooling_slope_rating" in expected:
            assert elec.cooling_slope.rating == expected["cooling_slope_rating"]
            assert elec.cooling_slope.percentile == pytest.approx(
                expected["cooling_slope_percentile"], abs=5.0  # Wider tolerance for slope
            )

        # Only test fossil fuel benchmarks if building has it
        if building_config["has_fossil_fuel"]:
            fossil = benchmark_results.FOSSIL_FUEL
            ff_expected = building_config["expected"]["fossil_fuel"]

            assert fossil.heating_slope.rating == ff_expected["heating_slope_rating"]
            assert fossil.heating_slope.percentile == pytest.approx(
                ff_expected["heating_slope_percentile"], abs=2.0
            )

            assert fossil.heating_change_point.rating == ff_expected["heating_change_point_rating"]
            assert fossil.heating_change_point.percentile == pytest.approx(
                ff_expected["heating_change_point_percentile"], abs=2.0
            )

            assert fossil.baseload.rating == ff_expected["baseload_rating"]
            assert fossil.baseload.percentile == pytest.approx(
                ff_expected["baseload_percentile"], abs=2.0
            )

    def test_04_recommendations(self, building_config, recommendations):
        """Test EE measure recommendations - must match Django output exactly."""
        rec_config = building_config["expected"]["recommendations"]

        # Extract recommendation IDs from actual results
        actual_rec_ids = [rec.measure_id for rec in recommendations.recommendations]
        expected_rec_ids = rec_config["expected_measures"]

        # Verify EXACT match - same recommendations, same count, no extras, no missing
        assert set(actual_rec_ids) == set(expected_rec_ids), (
            f"Recommendations do not match exactly!\n"
            f"Expected ({len(expected_rec_ids)}): {sorted(expected_rec_ids)}\n"
            f"Got ({len(actual_rec_ids)}): {sorted(actual_rec_ids)}\n"
            f"Missing: {set(expected_rec_ids) - set(actual_rec_ids)}\n"
            f"Extra: {set(actual_rec_ids) - set(expected_rec_ids)}"
        )

        # Also verify the count matches (redundant but explicit)
        assert len(actual_rec_ids) == rec_config["expected_count"], (
            f"Expected exactly {rec_config['expected_count']} recommendations, "
            f"got {len(actual_rec_ids)}"
        )

    def test_05_savings_estimation(self, building_config, savings):
        """Test energy and cost savings estimation."""
        # Validate ELECTRICITY savings (always present)
        elec_savings = savings.per_fuel["ELECTRICITY"]
        expected = building_config["expected"]["electricity"]

        # Energy savings percentage
        assert elec_savings.energy_savings_percent == pytest.approx(
            expected["energy_savings_percent"], abs=1.0  # Allow 1% tolerance
        )

        # Cost savings components
        baseload_cost = elec_savings.component_savings.cost_usd.baseload
        cooling_cost = elec_savings.component_savings.cost_usd.cooling_sensitive

        assert baseload_cost == pytest.approx(
            expected["baseload_cost_savings"], rel=0.02  # Allow 2% tolerance
        )
        assert cooling_cost == pytest.approx(
            expected["cooling_cost_savings"], rel=0.05  # Allow 5% tolerance
        )

        # Energy savings kWh
        if "energy_savings_kwh" in expected:
            assert elec_savings.energy_savings_kwh == pytest.approx(
                expected["energy_savings_kwh"], rel=0.02
            )

        # Fossil fuel savings (only for buildings that have it)
        if building_config["has_fossil_fuel"]:
            fossil_savings = savings.per_fuel["FOSSIL_FUEL"]
            ff_expected = building_config["expected"]["fossil_fuel"]

            assert fossil_savings.energy_savings_percent == pytest.approx(
                ff_expected["energy_savings_percent"], abs=1.0
            )

            heating_cost = fossil_savings.component_savings.cost_usd.heating_sensitive
            assert heating_cost == pytest.approx(ff_expected["heating_cost_savings"], rel=0.05)

        # Combined savings
        combined_expected = building_config["expected"]["combined"]
        assert savings.combined.energy_savings_kwh == pytest.approx(
            combined_expected["energy_savings_kwh"], rel=0.02
        )
        assert savings.combined.energy_savings_percent == pytest.approx(
            combined_expected["energy_savings_percent"], abs=1.0
        )

    def test_06_end_to_end_workflow(self, building_config, calendarized_data):
        """Test complete end-to-end workflow in a single test."""
        # Step 1: Fit change-point models
        cp_results = fit_calendarized_models(calendarized_data)
        assert "ELECTRICITY" in cp_results

        if building_config["has_fossil_fuel"]:
            assert "FOSSIL_FUEL" in cp_results

        # Step 2: Benchmark against reference
        benchmark = benchmark_with_reference(
            change_point_results=cp_results,
            floor_area=building_config["floor_area"],
            country_code=building_config["country_code"],
            building_type=building_config["building_type"],
        )
        assert benchmark.ELECTRICITY is not None

        if building_config["has_fossil_fuel"]:
            assert benchmark.FOSSIL_FUEL is not None

        # Step 3: Generate recommendations
        recs = recommend_ee_measures(benchmark, building_type=building_config["building_type"])
        assert len(recs.recommendations) > 0

        # Step 4: Estimate savings
        savings = estimate_savings(
            benchmark,
            calendarized_data,
            floor_area=building_config["floor_area"],
            savings_target=benchmark.savings_target,
        )
        assert savings.combined.energy_savings_kwh > 0
        assert savings.combined.energy_savings_percent > 0

        # Verify data flows correctly
        assert savings.per_fuel["ELECTRICITY"].valid

        if building_config["has_fossil_fuel"]:
            assert savings.per_fuel["FOSSIL_FUEL"].valid
