"""Statistical calculation functions for model evaluation."""

import math

import numpy as np
from scipy import stats

from better_lbnl_os.models.benchmarking import CoefficientBenchmarkStatistics


def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared (coefficient of determination).

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        R-squared value between 0 and 1
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 0.0

    r_squared = 1 - (ss_res / ss_tot)
    return max(0.0, min(1.0, r_squared))


def calculate_cvrmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Coefficient of Variation of RMSE.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        CV(RMSE) value
    """
    if len(y_true) == 0:
        return float("inf")

    mean_true = np.mean(y_true)
    if mean_true == 0:
        return float("inf")

    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    cvrmse = rmse / mean_true

    return cvrmse


def calculate_nmbe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Normalized Mean Bias Error.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        NMBE value
    """
    if len(y_true) == 0:
        return 0.0

    mean_true = np.mean(y_true)
    if mean_true == 0:
        return 0.0

    bias = np.mean(y_pred - y_true)
    nmbe = bias / mean_true

    return nmbe


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Percentage Error.

    Args:
        y_true: True values
        y_pred: Predicted values

    Returns:
        MAPE value as percentage
    """
    if len(y_true) == 0:
        return 0.0

    # Avoid division by zero
    mask = y_true != 0
    if not np.any(mask):
        return 0.0

    ape = np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])
    mape = np.mean(ape) * 100

    return mape


def calculate_percentile_from_z_score(z_score: float) -> float:
    """Convert z-score to percentile using normal distribution.

    Args:
        z_score: Standardized score

    Returns:
        Percentile value (0-100)
    """
    return round(stats.norm.cdf(z_score) * 100, 1)


def calculate_coefficient_statistics(
    coefficient_values: list[float],
) -> CoefficientBenchmarkStatistics:
    """Calculate median and robust standard deviation for a coefficient.

    Uses median absolute deviation (MAD) scaled to approximate standard deviation
    for robust statistics that are less sensitive to outliers.

    Args:
        coefficient_values: List of coefficient values from multiple buildings

    Returns:
        CoefficientBenchmarkStatistics with median and standard deviation
    """
    if not coefficient_values:
        return CoefficientBenchmarkStatistics()

    # Filter out None values
    valid_values = [v for v in coefficient_values if v is not None]

    if not valid_values:
        return CoefficientBenchmarkStatistics()

    try:
        # Calculate median
        median = float(np.median(valid_values))

        # Calculate robust standard deviation using median absolute deviation
        # Scale by 1.4826 to approximate standard deviation for normal distribution
        mad = stats.median_abs_deviation(valid_values)
        stdev = float(mad * 1.4826)

        # Handle NaN values
        if math.isnan(median):
            median = None
        if math.isnan(stdev):
            stdev = None

        return CoefficientBenchmarkStatistics(median=median, stdev=stdev)

    except Exception:
        return CoefficientBenchmarkStatistics()


def calculate_z_score(value: float, median: float, stdev: float) -> float:
    """Calculate z-score for a value given median and standard deviation.

    Args:
        value: Value to standardize
        median: Reference median
        stdev: Reference standard deviation

    Returns:
        Z-score (clamped to reasonable range for visualization)
    """
    if stdev == 0:
        return 0.0

    z_score = (value - median) / stdev

    # Clamp to reasonable range for visualization (99.99% confidence interval)
    if abs(z_score) > 3.45:
        z_score = 3.45 * np.sign(z_score)

    return z_score


def assign_performance_rating(z_score: float) -> str:
    """Assign performance rating based on z-score.

    Args:
        z_score: Standardized score (negative is better for most coefficients)

    Returns:
        Performance rating string
    """
    if z_score < -1:
        return "Good"
    elif -1 <= z_score <= 1:
        return "Typical"
    else:
        return "Poor"
