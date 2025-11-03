"""Tests for benchmarking functionality."""

import pytest

from better_lbnl_os.core.benchmarking import (
    benchmark_building,
    benchmark_coefficient,
    create_statistics_from_models,
    get_target_coefficient_value,
)
from better_lbnl_os.core.changepoint import ChangePointModelResult
from better_lbnl_os.models.benchmarking import (
    BenchmarkStatistics,
    CoefficientBenchmarkStatistics,
    EnergyTypeBenchmarkStatistics,
)
from better_lbnl_os.utils.statistics import (
    assign_performance_rating,
    calculate_coefficient_statistics,
    calculate_percentile_from_z_score,
    calculate_z_score,
)


class TestStatisticalFunctions:
    """Test statistical utility functions."""

    def test_calculate_coefficient_statistics(self):
        """Test coefficient statistics calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = calculate_coefficient_statistics(values)

        assert stats.median == 3.0
        assert stats.stdev is not None
        assert stats.stdev > 0

    def test_calculate_coefficient_statistics_with_nones(self):
        """Test handling of None values."""
        values = [1.0, None, 3.0, None, 5.0]
        stats = calculate_coefficient_statistics(values)

        assert stats.median == 3.0
        assert stats.stdev is not None

    def test_calculate_coefficient_statistics_empty(self):
        """Test empty input."""
        stats = calculate_coefficient_statistics([])
        assert stats.median is None
        assert stats.stdev is None

    def test_calculate_z_score(self):
        """Test z-score calculation."""
        z = calculate_z_score(5.0, 3.0, 1.0)
        assert z == 2.0

    def test_calculate_z_score_zero_stdev(self):
        """Test z-score with zero standard deviation."""
        z = calculate_z_score(5.0, 3.0, 0.0)
        assert z == 0.0

    def test_calculate_percentile_from_z_score(self):
        """Test percentile calculation."""
        percentile = calculate_percentile_from_z_score(0.0)
        assert percentile == 50.0

    def test_assign_performance_rating(self):
        """Test performance rating assignment."""
        assert assign_performance_rating(-1.5) == "Good"
        assert assign_performance_rating(0.0) == "Typical"
        assert assign_performance_rating(1.5) == "Poor"


class TestBenchmarkingFunctions:
    """Test core benchmarking functions."""

    def test_get_target_coefficient_value_cooling_changepoint(self):
        """Test target calculation for cooling change point (higher is better)."""
        target = get_target_coefficient_value("cooling_change_point", 20.0, 22.0, 2.0, "NOMINAL")
        assert target == 22.0  # median

        target = get_target_coefficient_value("cooling_change_point", 20.0, 22.0, 2.0, "AGGRESSIVE")
        assert target == 23.0  # median + stdev/2

    def test_get_target_coefficient_value_baseload(self):
        """Test target calculation for baseload (lower is better)."""
        target = get_target_coefficient_value("baseload", 5.0, 3.0, 1.0, "NOMINAL")
        assert target == 3.0  # median

        target = get_target_coefficient_value("baseload", 5.0, 3.0, 1.0, "AGGRESSIVE")
        assert target == 2.5  # median - stdev/2

    def test_benchmark_coefficient(self):
        """Test single coefficient benchmarking."""
        result = benchmark_coefficient(
            coefficient_name="baseload",
            coefficient_value=4.0,
            median=3.0,
            stdev=1.0,
            savings_target="NOMINAL",
            floor_area=1000.0,
        )

        assert result.coefficient_value == 4.0
        assert result.coefficient_value_with_area == 4000.0
        assert result.sample_median == 3.0
        assert result.sample_standard_deviation == 1.0
        assert result.rating in ["Good", "Typical", "Poor"]
        assert 0 <= result.percentile <= 100
        assert result.target_value is not None

    def test_benchmark_coefficient_missing_data(self):
        """Test benchmarking with missing data."""
        result = benchmark_coefficient(
            coefficient_name="baseload",
            coefficient_value=None,
            median=3.0,
            stdev=1.0,
            savings_target="NOMINAL",
            floor_area=1000.0,
        )

        assert result.coefficient_value is None
        assert result.rating is None
        assert result.percentile is None

    def test_create_statistics_from_models(self):
        """Test creating statistics from change-point models."""
        models = [
            ChangePointModelResult(
                heating_slope=-0.01,
                heating_change_point=15.0,
                baseload=2.0,
                cooling_change_point=22.0,
                cooling_slope=0.02,
                r_squared=0.8,
                cvrmse=0.2,
                model_type="5P",
            ),
            ChangePointModelResult(
                heating_slope=-0.02,
                heating_change_point=16.0,
                baseload=2.5,
                cooling_change_point=21.0,
                cooling_slope=0.03,
                r_squared=0.7,
                cvrmse=0.3,
                model_type="5P",
            ),
        ]

        stats = create_statistics_from_models(models)

        assert isinstance(stats, BenchmarkStatistics)
        assert stats.ELECTRICITY is not None
        assert stats.FOSSIL_FUEL is not None

    def test_benchmark_building(self):
        """Test complete building benchmarking."""
        # Create change-point results
        cp_results = {
            "ELECTRICITY": ChangePointModelResult(
                heating_slope=None,
                heating_change_point=None,
                baseload=2.0,
                cooling_change_point=22.0,
                cooling_slope=0.02,
                r_squared=0.8,
                cvrmse=0.2,
                model_type="3P-C",
            )
        }

        # Create benchmark statistics
        electricity_stats = EnergyTypeBenchmarkStatistics(
            baseload=CoefficientBenchmarkStatistics(median=2.5, stdev=0.5),
            cooling_change_point=CoefficientBenchmarkStatistics(median=21.0, stdev=2.0),
            cooling_slope=CoefficientBenchmarkStatistics(median=0.025, stdev=0.01),
        )

        benchmark_stats = BenchmarkStatistics(ELECTRICITY=electricity_stats)

        # Benchmark the building
        result = benchmark_building(
            change_point_results=cp_results,
            benchmark_statistics=benchmark_stats,
            floor_area=1000.0,
            savings_target="NOMINAL",
            building_id="test_building",
        )

        assert result.building_id == "test_building"
        assert result.floor_area == 1000.0
        assert result.savings_target == "NOMINAL"
        assert result.ELECTRICITY is not None
        assert result.ELECTRICITY.baseload is not None
        assert result.ELECTRICITY.baseload.rating in ["Good", "Typical", "Poor"]

    def test_benchmark_building_invalid_inputs(self):
        """Test benchmarking with invalid inputs."""
        with pytest.raises(ValueError):
            benchmark_building({}, None, 1000.0)

        with pytest.raises(ValueError):
            benchmark_building({}, BenchmarkStatistics(), 0.0)


if __name__ == "__main__":
    pytest.main([__file__])
