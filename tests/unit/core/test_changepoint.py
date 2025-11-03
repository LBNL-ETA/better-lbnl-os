"""
Tests for change-point modeling algorithms.
"""

import numpy as np
import pytest

from better_lbnl_os.core.changepoint import (
    _validate_model_inputs,
    calculate_cvrmse,
    calculate_r_squared,
    fit_changepoint_model,
    piecewise_linear_5p,
)
from better_lbnl_os.models import ChangePointModelResult


class TestChangePointModeling:
    """Test suite for change-point modeling functionality."""

    def test_validate_inputs_valid_data(self):
        """Test input validation with valid data."""
        temperature = np.array([10, 15, 20, 25, 30])
        energy_use = np.array([100, 90, 80, 90, 110])

        # Should not raise any exception
        _validate_model_inputs(temperature, energy_use)

    def test_validate_inputs_mismatched_lengths(self):
        """Test input validation with mismatched array lengths."""
        temperature = np.array([10, 15, 20])
        energy_use = np.array([100, 90])

        with pytest.raises(ValueError, match="same length"):
            _validate_model_inputs(temperature, energy_use)

    def test_validate_inputs_empty_arrays(self):
        """Test input validation with empty arrays."""
        temperature = np.array([])
        energy_use = np.array([])

        with pytest.raises(ValueError):
            _validate_model_inputs(temperature, energy_use)

    def test_validate_inputs_all_nan_temperature(self):
        """Test input validation with all NaN temperature data."""
        temperature = np.array([np.nan, np.nan, np.nan])
        energy_use = np.array([100, 90, 80])

        with pytest.raises(ValueError, match="cannot be all NaN"):
            _validate_model_inputs(temperature, energy_use)


class TestPiecewiseLinearFunction:
    """Test suite for the 5-parameter piecewise linear function."""

    def test_1p_model(self):
        """Test 1P (baseload only) model."""
        x = np.array([10, 15, 20, 25, 30])
        baseload = 85.0

        result = piecewise_linear_5p(x, None, None, baseload, None, None)
        expected = np.full_like(x, baseload)

        np.testing.assert_array_equal(result, expected)

    def test_3p_heating_model(self):
        """Test 3P heating model."""
        x = np.array([10, 15, 20, 25, 30])
        heating_slope = -2.0
        heating_changepoint = 18.0
        baseload = 80.0

        result = piecewise_linear_5p(x, heating_slope, heating_changepoint, baseload, None, None)

        # Check specific points
        # Below heating changepoint (10°C): should follow heating slope
        assert result[0] == heating_slope * 10 + baseload - heating_slope * heating_changepoint

        # Above heating changepoint (25°C): should be baseload
        assert result[3] == baseload

    def test_3p_cooling_model(self):
        """Test 3P cooling model."""
        x = np.array([10, 15, 20, 25, 30])
        cooling_slope = 3.0
        cooling_changepoint = 22.0
        baseload = 80.0

        result = piecewise_linear_5p(x, None, None, baseload, cooling_changepoint, cooling_slope)

        # Below cooling changepoint (20°C): should be baseload
        assert result[2] == baseload

        # Above cooling changepoint (30°C): should follow cooling slope
        assert result[4] == cooling_slope * 30 + baseload - cooling_slope * cooling_changepoint

    def test_5p_model(self):
        """Test full 5P model."""
        x = np.array([5, 15, 20, 25, 35])
        heating_slope = -2.0
        heating_changepoint = 12.0
        baseload = 80.0
        cooling_changepoint = 24.0
        cooling_slope = 3.0

        result = piecewise_linear_5p(
            x, heating_slope, heating_changepoint, baseload, cooling_changepoint, cooling_slope
        )

        # Check each regime
        # Heating: x[0] = 5 < 12
        expected_heating = heating_slope * 5 + baseload - heating_slope * heating_changepoint
        assert abs(result[0] - expected_heating) < 1e-10

        # Baseload: x[2] = 20, between 12 and 24
        assert result[2] == baseload

        # Cooling: x[4] = 35 > 24
        expected_cooling = cooling_slope * 35 + baseload - cooling_slope * cooling_changepoint
        assert abs(result[4] - expected_cooling) < 1e-10


class TestStatisticalFunctions:
    """Test suite for statistical calculation functions."""

    def test_calculate_r_squared_perfect_fit(self):
        """Test R² calculation with perfect fit."""
        y_actual = np.array([1, 2, 3, 4, 5])
        y_predicted = np.array([1, 2, 3, 4, 5])

        r2 = calculate_r_squared(y_actual, y_predicted)
        assert abs(r2 - 1.0) < 1e-10

    def test_calculate_r_squared_no_fit(self):
        """Test R² calculation with no predictive power."""
        y_actual = np.array([1, 2, 3, 4, 5])
        y_predicted = np.full_like(y_actual, np.mean(y_actual))

        r2 = calculate_r_squared(y_actual, y_predicted)
        assert abs(r2 - 0.0) < 1e-10

    def test_calculate_r_squared_invalid_inputs(self):
        """Test R² calculation with invalid inputs."""
        y_actual = np.array([])
        y_predicted = np.array([])

        with pytest.raises(ValueError):
            calculate_r_squared(y_actual, y_predicted)

    def test_calculate_r_squared_no_variance(self):
        """Test R² calculation when actual values have no variance."""
        y_actual = np.array([5, 5, 5, 5, 5])  # No variance
        y_predicted = np.array([5, 5, 5, 5, 5])  # Perfect prediction

        # When actual has no variance but prediction is perfect, R² = 1
        r2 = calculate_r_squared(y_actual, y_predicted)
        assert r2 == 1.0

        # When actual has no variance and prediction differs, R² = 0
        y_predicted_diff = np.array([4, 5, 6, 4, 6])
        r2_diff = calculate_r_squared(y_actual, y_predicted_diff)
        assert r2_diff == 0.0

    def test_calculate_cvrmse(self):
        """Test CV-RMSE calculation."""
        y_actual = np.array([100, 90, 80, 90, 110])
        y_predicted = np.array([95, 85, 85, 95, 105])

        cvrmse = calculate_cvrmse(y_actual, y_predicted)

        # Calculate expected CV-RMSE manually
        rmse = np.sqrt(np.mean((y_actual - y_predicted) ** 2))
        expected_cvrmse = rmse / np.mean(y_actual)

        assert abs(cvrmse - expected_cvrmse) < 1e-10


class TestChangePointModelIntegration:
    """Integration tests for full change-point model fitting."""

    def test_fit_simple_1p_model(self):
        """Test fitting a simple 1P model with constant data."""
        # Create constant energy use data (should result in 1P model)
        temperature = np.array([10, 15, 20, 25, 30])
        energy_use = np.array([85, 85, 85, 85, 85])

        result = fit_changepoint_model(temperature, energy_use)

        assert isinstance(result, ChangePointModelResult)
        assert result.model_type == "1P"
        assert abs(result.baseload - 85.0) < 1e-6
        assert result.heating_slope is None
        assert result.cooling_slope is None
        assert result.r_squared >= 0  # Should be defined

    def test_fit_model_with_heating_trend(self):
        """Test fitting model with clear heating trend."""
        # Create synthetic data with heating relationship
        temperature = np.linspace(5, 25, 20)
        baseload = 80
        heating_slope = -2.0
        heating_changepoint = 18.0

        # Generate synthetic energy use with heating trend
        energy_use = np.where(
            temperature < heating_changepoint,
            heating_slope * temperature + baseload - heating_slope * heating_changepoint,
            baseload,
        )

        # Add small amount of noise to make it realistic
        np.random.seed(42)
        energy_use += np.random.normal(0, 1, len(energy_use))

        result = fit_changepoint_model(temperature, energy_use)

        assert isinstance(result, ChangePointModelResult)
        # Should detect heating relationship (3P-H or 5P)
        assert result.model_type in ["3P Heating", "5P"]
        assert result.heating_slope is not None
        assert result.heating_slope < 0  # Should be negative for heating
        assert result.r_squared > 0.8  # Should have good fit

    def test_fit_model_insufficient_data(self):
        """Test behavior with insufficient data points."""
        temperature = np.array([20])  # Only one point
        energy_use = np.array([85])

        with pytest.raises(Exception):
            fit_changepoint_model(temperature, energy_use)


class TestChangePointModelResult:
    """Test suite for ChangePointModelResult domain model."""

    def test_model_validation_valid_model(self):
        """Test model validation with good quality model."""
        result = ChangePointModelResult(
            model_type="3P Heating",
            heating_slope=-2.0,
            heating_change_point=18.0,
            baseload=80.0,
            cooling_change_point=None,
            cooling_slope=None,
            r_squared=0.85,
            cvrmse=0.15,
        )

        assert result.is_valid()
        assert result.get_model_complexity() == 3

    def test_model_validation_poor_quality(self):
        """Test model validation with poor quality model."""
        result = ChangePointModelResult(
            model_type="1P",
            heating_slope=None,
            heating_change_point=None,
            baseload=80.0,
            cooling_change_point=None,
            cooling_slope=None,
            r_squared=0.3,  # Poor R²
            cvrmse=0.8,  # High CV-RMSE
        )

        assert not result.is_valid()

    def test_annual_consumption_estimation(self):
        """Test annual consumption estimation from degree days."""
        result = ChangePointModelResult(
            model_type="5P",
            heating_slope=-2.0,
            heating_change_point=18.0,
            baseload=80.0,
            cooling_change_point=24.0,
            cooling_slope=3.0,
            r_squared=0.85,
            cvrmse=0.15,
        )

        annual_hdd = 1000  # Heating degree days
        annual_cdd = 500  # Cooling degree days

        annual_consumption = result.estimate_annual_consumption(annual_hdd, annual_cdd)

        # Manual calculation
        expected = 80.0 * 365 + (-2.0) * 1000 + 3.0 * 500
        assert abs(annual_consumption - expected) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__])
