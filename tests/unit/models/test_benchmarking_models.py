"""Unit tests for benchmarking data models."""

import pytest

from better_lbnl_os.models.benchmarking import (
    BenchmarkResult,
    BenchmarkStatistics,
    CoefficientBenchmarkResult,
    CoefficientBenchmarkStatistics,
    EnergyTypeBenchmarkResult,
    EnergyTypeBenchmarkStatistics,
)


class TestCoefficientBenchmarkStatistics:
    """Test CoefficientBenchmarkStatistics model."""

    def test_creation(self):
        """Test creating CoefficientBenchmarkStatistics."""
        stats = CoefficientBenchmarkStatistics(median=3.0, stdev=1.0)
        assert stats.median == 3.0
        assert stats.stdev == 1.0

    def test_optional_fields(self):
        """Test that fields can be None."""
        stats = CoefficientBenchmarkStatistics()
        assert stats.median is None
        assert stats.stdev is None


class TestEnergyTypeBenchmarkStatistics:
    """Test EnergyTypeBenchmarkStatistics model."""

    def test_creation(self):
        """Test creating EnergyTypeBenchmarkStatistics."""
        stats = EnergyTypeBenchmarkStatistics(
            baseload=CoefficientBenchmarkStatistics(median=2.0, stdev=0.5),
            heating_slope=CoefficientBenchmarkStatistics(median=-0.01, stdev=0.005),
        )
        assert stats.baseload.median == 2.0
        assert stats.heating_slope.median == -0.01

    def test_all_fields_optional(self):
        """Test that all coefficient fields are optional."""
        stats = EnergyTypeBenchmarkStatistics()
        assert stats.baseload is None
        assert stats.heating_slope is None
        assert stats.cooling_slope is None


class TestBenchmarkStatistics:
    """Test BenchmarkStatistics model."""

    def test_creation(self):
        """Test creating BenchmarkStatistics."""
        elec_stats = EnergyTypeBenchmarkStatistics(
            baseload=CoefficientBenchmarkStatistics(median=2.0, stdev=0.5)
        )
        stats = BenchmarkStatistics(ELECTRICITY=elec_stats)
        assert stats.ELECTRICITY is not None
        assert stats.ELECTRICITY.baseload.median == 2.0

    def test_both_energy_types(self):
        """Test creating statistics for both energy types."""
        elec_stats = EnergyTypeBenchmarkStatistics(
            baseload=CoefficientBenchmarkStatistics(median=2.0, stdev=0.5)
        )
        fossil_stats = EnergyTypeBenchmarkStatistics(
            heating_slope=CoefficientBenchmarkStatistics(median=-0.02, stdev=0.01)
        )
        stats = BenchmarkStatistics(ELECTRICITY=elec_stats, FOSSIL_FUEL=fossil_stats)
        assert stats.ELECTRICITY is not None
        assert stats.FOSSIL_FUEL is not None


class TestCoefficientBenchmarkResult:
    """Test CoefficientBenchmarkResult model."""

    def test_creation(self):
        """Test creating CoefficientBenchmarkResult."""
        result = CoefficientBenchmarkResult(
            coefficient_value=4.0,
            coefficient_value_with_area=4000.0,
            rating="Poor",
            percentile=75.0,
            sample_median=3.0,
            sample_standard_deviation=1.0,
            target_value=3.0,
        )
        assert result.coefficient_value == 4.0
        assert result.rating == "Poor"
        assert result.percentile == 75.0

    def test_percentile_validation(self):
        """Test that percentile is validated between 0 and 100."""
        # Valid percentiles
        result = CoefficientBenchmarkResult(percentile=0.0)
        assert result.percentile == 0.0

        result = CoefficientBenchmarkResult(percentile=100.0)
        assert result.percentile == 100.0

        # Invalid percentile
        with pytest.raises(Exception):  # Pydantic validation error
            CoefficientBenchmarkResult(percentile=150.0)


class TestEnergyTypeBenchmarkResult:
    """Test EnergyTypeBenchmarkResult model."""

    def test_creation(self):
        """Test creating EnergyTypeBenchmarkResult."""
        baseload_result = CoefficientBenchmarkResult(
            coefficient_value=2.0,
            rating="Good",
            percentile=25.0,
        )
        result = EnergyTypeBenchmarkResult(baseload=baseload_result)
        assert result.baseload is not None
        assert result.baseload.rating == "Good"

    def test_multiple_coefficients(self):
        """Test result with multiple coefficients."""
        result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0, rating="Good"),
            heating_slope=CoefficientBenchmarkResult(coefficient_value=-0.01, rating="Typical"),
            cooling_slope=CoefficientBenchmarkResult(coefficient_value=0.02, rating="Poor"),
        )
        assert result.baseload.rating == "Good"
        assert result.heating_slope.rating == "Typical"
        assert result.cooling_slope.rating == "Poor"


class TestBenchmarkResult:
    """Test BenchmarkResult model."""

    def test_creation(self):
        """Test creating BenchmarkResult."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0, rating="Good")
        )
        result = BenchmarkResult(
            building_id="test_building",
            floor_area=1000.0,
            savings_target="NOMINAL",
            ELECTRICITY=elec_result,
        )
        assert result.building_id == "test_building"
        assert result.floor_area == 1000.0
        assert result.savings_target == "NOMINAL"

    def test_floor_area_validation(self):
        """Test that floor_area must be positive."""
        # Valid floor area
        result = BenchmarkResult(floor_area=1000.0)
        assert result.floor_area == 1000.0

        # Invalid floor area (zero or negative)
        with pytest.raises(Exception):  # Pydantic validation error
            BenchmarkResult(floor_area=0.0)

        with pytest.raises(Exception):
            BenchmarkResult(floor_area=-100.0)

    def test_get_overall_rating_single_coefficient(self):
        """Test get_overall_rating with single coefficient."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0, rating="Good")
        )
        result = BenchmarkResult(ELECTRICITY=elec_result)

        overall = result.get_overall_rating("ELECTRICITY")
        assert overall == "Good"

    def test_get_overall_rating_multiple_coefficients(self):
        """Test get_overall_rating with multiple coefficients."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0, rating="Good"),
            heating_slope=CoefficientBenchmarkResult(coefficient_value=-0.01, rating="Good"),
            cooling_slope=CoefficientBenchmarkResult(coefficient_value=0.02, rating="Poor"),
        )
        result = BenchmarkResult(ELECTRICITY=elec_result)

        overall = result.get_overall_rating("ELECTRICITY")
        assert overall == "Good"  # Majority vote: 2 Good, 1 Poor

    def test_get_overall_rating_tie(self):
        """Test get_overall_rating when there's a tie."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0, rating="Good"),
            cooling_slope=CoefficientBenchmarkResult(coefficient_value=0.02, rating="Poor"),
        )
        result = BenchmarkResult(ELECTRICITY=elec_result)

        overall = result.get_overall_rating("ELECTRICITY")
        # With a tie, max() will return one of them (deterministic based on dict order)
        assert overall in ["Good", "Poor"]

    def test_get_overall_rating_no_energy_type(self):
        """Test get_overall_rating when energy type doesn't exist."""
        result = BenchmarkResult()
        overall = result.get_overall_rating("ELECTRICITY")
        assert overall is None

    def test_get_overall_rating_no_coefficients(self):
        """Test get_overall_rating when no coefficients have ratings."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0)  # No rating
        )
        result = BenchmarkResult(ELECTRICITY=elec_result)

        overall = result.get_overall_rating("ELECTRICITY")
        assert overall is None

    def test_get_overall_rating_fossil_fuel(self):
        """Test get_overall_rating for FOSSIL_FUEL energy type."""
        fossil_result = EnergyTypeBenchmarkResult(
            heating_slope=CoefficientBenchmarkResult(coefficient_value=-0.02, rating="Typical")
        )
        result = BenchmarkResult(FOSSIL_FUEL=fossil_result)

        overall = result.get_overall_rating("FOSSIL_FUEL")
        assert overall == "Typical"

    def test_get_average_percentile_single_coefficient(self):
        """Test get_average_percentile with single coefficient."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0, percentile=25.0)
        )
        result = BenchmarkResult(ELECTRICITY=elec_result)

        avg = result.get_average_percentile("ELECTRICITY")
        assert avg == 25.0

    def test_get_average_percentile_multiple_coefficients(self):
        """Test get_average_percentile with multiple coefficients."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0, percentile=20.0),
            heating_slope=CoefficientBenchmarkResult(coefficient_value=-0.01, percentile=40.0),
            cooling_slope=CoefficientBenchmarkResult(coefficient_value=0.02, percentile=60.0),
        )
        result = BenchmarkResult(ELECTRICITY=elec_result)

        avg = result.get_average_percentile("ELECTRICITY")
        assert avg == 40.0  # (20 + 40 + 60) / 3

    def test_get_average_percentile_no_energy_type(self):
        """Test get_average_percentile when energy type doesn't exist."""
        result = BenchmarkResult()
        avg = result.get_average_percentile("ELECTRICITY")
        assert avg is None

    def test_get_average_percentile_no_percentiles(self):
        """Test get_average_percentile when no coefficients have percentiles."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0)  # No percentile
        )
        result = BenchmarkResult(ELECTRICITY=elec_result)

        avg = result.get_average_percentile("ELECTRICITY")
        assert avg is None

    def test_get_average_percentile_mixed_data(self):
        """Test get_average_percentile with some missing percentiles."""
        elec_result = EnergyTypeBenchmarkResult(
            baseload=CoefficientBenchmarkResult(coefficient_value=2.0, percentile=30.0),
            heating_slope=CoefficientBenchmarkResult(coefficient_value=-0.01),  # No percentile
            cooling_slope=CoefficientBenchmarkResult(coefficient_value=0.02, percentile=70.0),
        )
        result = BenchmarkResult(ELECTRICITY=elec_result)

        avg = result.get_average_percentile("ELECTRICITY")
        assert avg == 50.0  # (30 + 70) / 2, ignoring the None

    def test_get_average_percentile_fossil_fuel(self):
        """Test get_average_percentile for FOSSIL_FUEL energy type."""
        fossil_result = EnergyTypeBenchmarkResult(
            heating_slope=CoefficientBenchmarkResult(coefficient_value=-0.02, percentile=50.0)
        )
        result = BenchmarkResult(FOSSIL_FUEL=fossil_result)

        avg = result.get_average_percentile("FOSSIL_FUEL")
        assert avg == 50.0
