import math

import numpy as np
import pytest

from better_lbnl_os.models.benchmarking import CoefficientBenchmarkStatistics
from better_lbnl_os.utils import statistics


def test_calculate_r_squared_handles_perfect_and_constant_series():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    assert statistics.calculate_r_squared(y_true, y_pred) == pytest.approx(1.0)

    constant = np.array([5.0, 5.0, 5.0])
    assert statistics.calculate_r_squared(constant, constant) == 0.0


def test_calculate_cvrmse_handles_edge_cases():
    y_true = np.array([10.0, 12.0, 14.0])
    y_pred = np.array([9.0, 13.0, 15.0])
    value = statistics.calculate_cvrmse(y_true, y_pred)
    assert value == pytest.approx(0.083333, rel=1e-5)

    assert math.isinf(statistics.calculate_cvrmse(np.array([]), np.array([])))
    assert math.isinf(statistics.calculate_cvrmse(np.array([0.0, 0.0]), np.array([1.0, 1.0])))


def test_calculate_nmbe_and_mape_behaviour():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0])
    assert statistics.calculate_nmbe(y_true, y_pred) == pytest.approx(0.05, rel=1e-6)
    assert statistics.calculate_mape(y_true, y_pred) == pytest.approx(13.333333, rel=1e-6)

    assert statistics.calculate_nmbe(np.array([]), np.array([])) == 0.0
    assert statistics.calculate_nmbe(np.array([0.0, 0.0]), np.array([1.0, 1.0])) == 0.0
    assert statistics.calculate_mape(np.array([0.0, 0.0]), np.array([1.0, 1.0])) == 0.0


def test_percentile_and_z_score_helpers():
    assert statistics.calculate_percentile_from_z_score(0.0) == pytest.approx(50.0, rel=1e-6)

    stats_result = statistics.calculate_coefficient_statistics([1.0, 2.0, 3.0, None])
    assert isinstance(stats_result, CoefficientBenchmarkStatistics)
    assert stats_result.median == pytest.approx(2.0, rel=1e-6)
    assert stats_result.stdev == pytest.approx(1.4826, rel=1e-4)

    empty_stats = statistics.calculate_coefficient_statistics([])
    assert empty_stats.median is None and empty_stats.stdev is None

    assert statistics.calculate_z_score(10.0, 0.0, 0.0) == 0.0
    assert statistics.calculate_z_score(5.0, 0.0, 2.0) == pytest.approx(2.5, rel=1e-6)
    assert statistics.calculate_z_score(10.0, 0.0, 1.0) == pytest.approx(3.45, rel=1e-6)

    assert statistics.assign_performance_rating(-2.0) == "Good"
    assert statistics.assign_performance_rating(0.5) == "Typical"
    assert statistics.assign_performance_rating(1.5) == "Poor"
