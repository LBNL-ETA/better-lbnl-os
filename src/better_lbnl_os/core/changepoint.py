"""Change-point model fitting algorithms for building energy analysis.

This module contains pure change-point modeling functions for statistical
analysis of energy consumption patterns with respect to temperature.
"""

from __future__ import annotations

import logging
from math import isclose

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from pydantic import BaseModel, Field
from scipy import optimize, stats

# ChangePointModelResult defined at end of file to avoid circular imports
from better_lbnl_os.constants import (
    DEFAULT_CVRMSE_THRESHOLD,
    DEFAULT_R2_THRESHOLD,
    DEFAULT_SIGNIFICANT_PVAL,
)

logger = logging.getLogger(__name__)

# Default thresholds now sourced from data.constants


def fit_changepoint_model(
    x: np.ndarray,
    y: np.ndarray,
    min_r_squared: float = DEFAULT_R2_THRESHOLD,
    max_cv_rmse: float = DEFAULT_CVRMSE_THRESHOLD,
) -> ChangePointModelResult:
    """Fit a change-point model to any x,y data relationship.

    This is the main entry point for change-point model fitting. It automatically
    determines the best model type (1P, 3P, or 5P) based on statistical significance
    and model quality metrics.

    Common usage examples:
    - Energy analysis: x=temperature, y=energy_use
    - Price analysis: x=price, y=demand
    - Time series: x=time, y=usage

    Args:
        x: Array of independent variable values (e.g., temperature, price, time)
        y: Array of dependent variable values (e.g., energy_use, demand, usage)
        min_r_squared: Minimum R² threshold for model acceptance
        max_cv_rmse: Maximum CV-RMSE threshold for model acceptance

    Returns:
        ChangePointModelResult with fitted coefficients and quality metrics

    Raises:
        ValueError: If input arrays are invalid or empty
        Exception: If model fitting fails
    """
    # Input validation
    _validate_model_inputs(x, y)

    # Check for constant or near-constant data (early 1P detection)
    # If data has no variance, skip changepoint fitting and use 1P model directly
    y_std = np.std(y)
    y_mean = np.mean(y)
    if y_std < 1e-6 or (y_mean != 0 and y_std / abs(y_mean) < 0.01):
        # Data is essentially constant, use 1P model (baseload only)
        return _fit_1p_model(x, y, max_cv_rmse)

    # Set up bounds for model fitting
    bounds = _create_model_bounds(x, y)

    # Try fitting with different change-point bounds
    search_bounds = _create_changepoint_search_bounds(x, n_bins=8)
    fit_results = []

    for cp_bounds in search_bounds:
        try:
            # Update bounds for this iteration
            iteration_bounds = bounds.copy()
            iteration_bounds[0][1] = cp_bounds[0][0]  # left changepoint lower
            iteration_bounds[1][1] = cp_bounds[0][1]  # left changepoint upper
            iteration_bounds[0][3] = cp_bounds[1][0]  # right changepoint lower
            iteration_bounds[1][3] = cp_bounds[1][1]  # right changepoint upper

            result = _fit_model_once(x, y, iteration_bounds)
            fit_results.append(result)

        except Exception:
            # Some bounds combinations may fail - this is expected
            continue

    if not fit_results:
        raise Exception("Could not fit any change-point model with given data")

    # Select best model and determine type
    optimal_model = _select_optimal_model(fit_results, x, y, min_r_squared, max_cv_rmse)

    return optimal_model


def _validate_model_inputs(x: np.ndarray, y: np.ndarray) -> None:
    """Validate inputs for change-point model fitting."""
    if not np.any(x):
        raise ValueError("x must have at least one element")
    if not np.any(y):
        raise ValueError("y must have at least one element")
    if np.size(y) != np.size(x):
        raise ValueError("x and y arrays must have the same length")
    if np.size(x) < 3:
        raise ValueError("Need at least 3 data points for change-point modeling")
    if all(np.isnan(x)):
        raise ValueError("x data cannot be all NaN")


def _create_model_bounds(x: np.ndarray, y: np.ndarray) -> list:
    """Create bounds for model coefficient optimization."""
    left_slope_bounds = [-np.inf, 0]  # left slope (negative for energy/temperature)
    left_cp_bounds = [np.min(x), np.max(x)]  # left changepoint
    baseline_bounds = [np.min(y), np.max(y)]  # baseline value
    right_cp_bounds = [np.min(x), np.max(x)]  # right changepoint
    right_slope_bounds = [0, np.inf]  # right slope (positive for energy/temperature)

    return [
        [
            left_slope_bounds[0],
            left_cp_bounds[0],
            baseline_bounds[0],
            right_cp_bounds[0],
            right_slope_bounds[0],
        ],
        [
            left_slope_bounds[1],
            left_cp_bounds[1],
            baseline_bounds[1],
            right_cp_bounds[1],
            right_slope_bounds[1],
        ],
    ]


def _create_changepoint_search_bounds(x: np.ndarray, n_bins: int = 4) -> list:
    """Create search bounds for left and right changepoints."""
    bin_width = np.ptp(x) / n_bins
    marks = [np.min(x) + i * bin_width for i in range(n_bins + 1)]

    bounds_list = []
    for i in range(len(marks) - 1):
        for j in range(i + 1, len(marks) - 1):
            bounds_list.append(
                [
                    (marks[i], marks[i + 1]),  # left changepoint bounds
                    (marks[j], marks[j + 1]),  # right changepoint bounds
                ]
            )

    return bounds_list


def _fit_model_once(x: np.ndarray, y: np.ndarray, bounds: list) -> dict:
    """Fit the piecewise linear model once with given bounds."""
    # Perform curve fitting
    popt, pcov = optimize.curve_fit(
        f=piecewise_linear_5p, xdata=x, ydata=y, bounds=bounds, method="dogbox"
    )

    # Calculate model quality metrics
    y_predicted = piecewise_linear_5p(x, *popt)
    r2 = calculate_r_squared(y, y_predicted)
    cvrmse = calculate_cvrmse(y, y_predicted)

    # Check slope significance
    pval_left, valid_left = _check_slope_significance(popt[0], x, y, popt, is_left_slope=True)
    pval_right, valid_right = _check_slope_significance(popt[4], x, y, popt, is_left_slope=False)

    return {
        "coefficients": popt,
        "covariance": pcov,
        "r_squared": r2,
        "cvrmse": cvrmse,
        "heating_pvalue": pval_left,  # Keep legacy key names for compatibility
        "cooling_pvalue": pval_right,
        "heating_significant": valid_left,
        "cooling_significant": valid_right,
    }


def _check_slope_significance(
    slope: float, x: np.ndarray, y: np.ndarray, coefficients: np.ndarray, is_left_slope: bool
) -> tuple[float | None, bool]:
    """Check if a left or right slope is statistically significant."""
    if isclose(slope, 0, abs_tol=1e-5):
        return None, False

    if is_left_slope:
        # Check left slope significance
        changepoint = coefficients[1]
        mask = x <= changepoint
    else:
        # Check right slope significance
        changepoint = coefficients[3]
        mask = x >= changepoint

    x_subset = x[mask]
    y_subset = y[mask]

    if len(x_subset) <= 2:
        return np.inf, False

    y_predicted = piecewise_linear_5p(x_subset, *coefficients)
    pvalue = _calculate_slope_pvalue(slope, x_subset, y_subset, y_predicted)

    return pvalue, pvalue < DEFAULT_SIGNIFICANT_PVAL


def _calculate_slope_pvalue(
    slope: float, x_data: np.ndarray, y_data: np.ndarray, y_predicted: np.ndarray
) -> float:
    """Calculate p-value for regression slope significance."""
    if len(x_data) <= 2:
        return np.inf

    # Calculate standard error of slope
    residuals = y_data - y_predicted
    sample_variance = np.sum(residuals**2) / (len(x_data) - 2)
    sum_squares_x = np.sum((x_data - np.mean(x_data)) ** 2)
    standard_error = np.sqrt(sample_variance / sum_squares_x)

    # Calculate t-statistic and p-value
    t_statistic = slope / standard_error
    pvalue = stats.t.sf(np.abs(t_statistic), len(x_data) - 1) * 2  # two-tailed test

    return pvalue


def _select_optimal_model(
    fit_results: list, x: np.ndarray, y: np.ndarray, min_r_squared: float, max_cv_rmse: float
) -> ChangePointModelResult:
    """Select the optimal model from fit results and determine model type."""
    # Convert results to DataFrame for easier analysis
    rows = []
    for result in fit_results:
        coeff = result["coefficients"]
        row = [
            coeff[0],
            coeff[1],
            coeff[2],
            coeff[3],
            coeff[4],  # coefficients
            result["r_squared"],
            result["cvrmse"],
            result["heating_pvalue"],
            result["cooling_pvalue"],
            result["heating_significant"],
            result["cooling_significant"],
        ]
        rows.append(row)

    df_fits = pd.DataFrame(
        rows,
        columns=[
            "heating_slope",
            "heating_changepoint",
            "baseload",
            "cooling_changepoint",
            "cooling_slope",
            "r_squared",
            "cvrmse",
            "heating_pvalue",
            "cooling_pvalue",
            "heating_significant",
            "cooling_significant",
        ],
    )

    # Filter for models with at least one significant slope
    df_significant = df_fits[(df_fits["heating_significant"]) | (df_fits["cooling_significant"])]

    if len(df_significant) > 0:
        # Select model with highest R²
        best_idx = df_significant["r_squared"].idxmax()
        best_model = df_significant.loc[best_idx]

        # Determine model type and validate
        model_type, coefficients = _determine_model_type(best_model, x, y, min_r_squared)

        if model_type != "No-fit":
            return ChangePointModelResult(
                model_type=model_type,
                heating_slope=coefficients.get("heating_slope"),
                heating_change_point=coefficients.get("heating_changepoint"),
                baseload=coefficients["baseload"],
                cooling_change_point=coefficients.get("cooling_changepoint"),
                cooling_slope=coefficients.get("cooling_slope"),
                r_squared=best_model["r_squared"],
                cvrmse=best_model["cvrmse"],
                heating_pvalue=best_model["heating_pvalue"],
                cooling_pvalue=best_model["cooling_pvalue"],
            )

    # Try 1P model as fallback
    return _fit_1p_model(x, y, max_cv_rmse)


def _determine_model_type(
    model_row: pd.Series, x: np.ndarray, y: np.ndarray, min_r_squared: float
) -> tuple[str, dict]:
    """Determine model type (5P, 3P, etc.) and extract coefficients."""
    heating_significant = model_row["heating_significant"]
    cooling_significant = model_row["cooling_significant"]

    if heating_significant and cooling_significant:
        # 5P model
        coefficients = {
            "heating_slope": model_row["heating_slope"],
            "heating_changepoint": model_row["heating_changepoint"],
            "baseload": model_row["baseload"],
            "cooling_changepoint": model_row["cooling_changepoint"],
            "cooling_slope": model_row["cooling_slope"],
        }

        # Validate R² threshold
        test_coeffs = [
            coefficients["heating_slope"],
            coefficients["heating_changepoint"],
            coefficients["baseload"],
            coefficients["cooling_changepoint"],
            coefficients["cooling_slope"],
        ]

        if _check_r2_threshold(x, y, test_coeffs, min_r_squared):
            return "5P", coefficients

    elif cooling_significant and not heating_significant:
        # 3P cooling model
        coefficients = {
            "heating_slope": None,
            "heating_changepoint": None,
            "baseload": model_row["baseload"],
            "cooling_changepoint": model_row["cooling_changepoint"],
            "cooling_slope": model_row["cooling_slope"],
        }

        test_coeffs = [
            None,
            None,
            coefficients["baseload"],
            coefficients["cooling_changepoint"],
            coefficients["cooling_slope"],
        ]

        if _check_r2_threshold(x, y, test_coeffs, min_r_squared):
            return "3P Cooling", coefficients

    elif heating_significant and not cooling_significant:
        # 3P heating model
        coefficients = {
            "heating_slope": model_row["heating_slope"],
            "heating_changepoint": model_row["heating_changepoint"],
            "baseload": model_row["baseload"],
            "cooling_changepoint": None,
            "cooling_slope": None,
        }

        test_coeffs = [
            coefficients["heating_slope"],
            coefficients["heating_changepoint"],
            coefficients["baseload"],
            None,
            None,
        ]

        if _check_r2_threshold(x, y, test_coeffs, min_r_squared):
            return "3P Heating", coefficients

    return "No-fit", {}


def _check_r2_threshold(
    x: np.ndarray, y: np.ndarray, coefficients: list, min_r_squared: float
) -> bool:
    """Check if model meets R² threshold."""
    predicted = piecewise_linear_5p(x, *coefficients)
    r2 = calculate_r_squared(y, predicted)
    return r2 >= min_r_squared


def _fit_1p_model(x: np.ndarray, y: np.ndarray, max_cv_rmse: float) -> ChangePointModelResult:
    """Fit a 1P (constant) model as fallback."""
    baseload = np.mean(y)
    predicted = np.full_like(y, baseload)

    r2 = calculate_r_squared(y, predicted)
    cvrmse = calculate_cvrmse(y, predicted)

    if cvrmse <= max_cv_rmse:
        model_type = "1P"
    else:
        model_type = "No-fit"

    return ChangePointModelResult(
        model_type=model_type,
        heating_slope=None,
        heating_change_point=None,
        baseload=baseload,
        cooling_change_point=None,
        cooling_slope=None,
        r_squared=r2,
        cvrmse=cvrmse,
        heating_pvalue=None,
        cooling_pvalue=None,
    )


def piecewise_linear_5p(
    x: np.ndarray,
    heating_slope: float | None,
    heating_changepoint: float | None,
    baseload: float,
    cooling_changepoint: float | None,
    cooling_slope: float | None,
) -> np.ndarray:
    r"""Five-parameter piecewise linear function for change-point modeling.

    This function implements the classic change-point model:
    - Heating slope (negative) below heating changepoint
    - Flat baseload between changepoints
    - Cooling slope (positive) above cooling changepoint

    Visual representation:

        k1  \              / k2
             \            /
        y0    \__________/
              cpL      cpR

    Where:
        k1 = heating_slope (typically negative)
        k2 = cooling_slope (typically positive)
        y0 = baseload (constant energy use)
        cpL = heating_changepoint
        cpR = cooling_changepoint

    Args:
        x: Temperature values
        heating_slope: Slope for heating regime (typically negative)
        heating_changepoint: Temperature where heating turns on
        baseload: Constant energy use in neutral zone
        cooling_changepoint: Temperature where cooling turns on
        cooling_slope: Slope for cooling regime (typically positive)

    Returns:
        Predicted energy use values
    """
    if baseload is None:
        return np.full_like(x, np.nan)

    # Handle 1P model (baseload only)
    if all(
        param is None or np.isnan(param)
        for param in [heating_slope, heating_changepoint, cooling_changepoint, cooling_slope]
    ):
        return np.full_like(x, baseload)

    # Handle 3P models by setting missing parameters
    if (
        heating_changepoint is None
        or heating_slope is None
        or np.isnan(heating_changepoint)
        or np.isnan(heating_slope)
    ):
        heating_changepoint = cooling_changepoint
        heating_slope = 0

    if (
        cooling_changepoint is None
        or cooling_slope is None
        or np.isnan(cooling_changepoint)
        or np.isnan(cooling_slope)
    ):
        cooling_changepoint = heating_changepoint
        cooling_slope = 0

    # Define conditions and functions for piecewise model
    conditions = [
        x < heating_changepoint,
        (x >= heating_changepoint) & (x <= cooling_changepoint),
        x > cooling_changepoint,
    ]

    functions = [
        lambda x: heating_slope * x + baseload - heating_slope * heating_changepoint,
        lambda x: baseload,
        lambda x: cooling_slope * x + baseload - cooling_slope * cooling_changepoint,
    ]

    return np.piecewise(x, conditions, functions)


def calculate_r_squared(y_actual: np.ndarray, y_predicted: np.ndarray | float) -> float:
    """Calculate R-squared (coefficient of determination).

    Args:
        y_actual: Actual values
        y_predicted: Predicted values

    Returns:
        R-squared value between 0 and 1

    Raises:
        ValueError: If inputs are invalid
        Exception: If there's no variance in actual values
    """
    if not isinstance(y_actual, np.ndarray):
        raise ValueError("y_actual must be a numpy array")
    if y_actual.size == 0:
        raise ValueError("y_actual cannot be empty")
    if not isinstance(y_predicted, (np.ndarray, float)):
        raise ValueError("y_predicted must be numpy array or float")
    if isinstance(y_predicted, np.ndarray) and y_predicted.size == 0:
        raise ValueError("y_predicted cannot be empty array")

    residuals = y_actual - y_predicted
    ss_residuals = np.sum(residuals**2)
    ss_total = np.sum((y_actual - np.mean(y_actual)) ** 2)

    # For constant data (no variance), R² is undefined but we return 0
    # This occurs when fitting 1P model to constant data
    if ss_total == 0:
        # If residuals are also 0 (perfect prediction of constant), return 1
        # Otherwise return 0 (model predicts mean, which is the best we can do)
        return 1.0 if ss_residuals == 0 else 0.0

    return 1 - (ss_residuals / ss_total)


def calculate_cvrmse(y_actual: np.ndarray, y_predicted: np.ndarray) -> float:
    """Calculate Coefficient of Variation of Root Mean Squared Error.

    Args:
        y_actual: Actual values
        y_predicted: Predicted values

    Returns:
        CV-RMSE value
    """
    rmse = np.sqrt(np.mean((y_actual - y_predicted) ** 2))
    mean_actual = np.mean(y_actual)

    return rmse / mean_actual if mean_actual != 0 else np.inf


def plot_changepoint_model(
    x: np.ndarray,
    y: np.ndarray,
    model_result: ChangePointModelResult,
    x_label: str = "X",
    y_label: str = "Y",
    title: str | None = None,
    figsize: tuple[int, int] = (12, 6),
    save_path: str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot change-point model results with data points and fitted line.

    Args:
        x: Independent variable data (e.g., temperature)
        y: Dependent variable data (e.g., energy use)
        model_result: Fitted change-point model result
        x_label: Label for x-axis
        y_label: Label for y-axis
        title: Plot title (auto-generated if None)
        figsize: Figure size tuple
        save_path: Path to save figure (optional)

    Returns:
        Figure and axes objects
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.subplots_adjust(right=0.75)

    # Always work with numpy arrays to avoid pandas indexing surprises
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    # Plot data points
    scatter = ax.scatter(x, y, alpha=0.6, s=30, c="k", label="Data")

    if model_result.model_type == "No-fit":
        ax.set_title(f"No valid model fit ({len(x)} data points)")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        return fig, ax

    # Create a smooth x-range for plotting the model curve
    x_min, x_max = np.min(x), np.max(x)
    # Guard against a single-point input which would collapse np.ptp
    span = np.ptp(x) or max(abs(x_min), 1.0)
    x_range = np.linspace(x_min - 0.05 * span, x_max + 0.05 * span, 300)
    y_range = piecewise_linear_5p(
        x_range,
        model_result.heating_slope,
        model_result.heating_change_point,
        model_result.baseload,
        model_result.cooling_change_point,
        model_result.cooling_slope,
    )

    # Adjust scale so plotted curve matches the units of provided y-values when they differ
    # (e.g., model fit on kWh/sqft/day but caller plots monthly EUI).
    pred_at_x = piecewise_linear_5p(
        x,
        model_result.heating_slope,
        model_result.heating_change_point,
        model_result.baseload,
        model_result.cooling_change_point,
        model_result.cooling_slope,
    )
    valid_mask = np.isfinite(pred_at_x) & np.isfinite(y)
    with np.errstate(invalid="ignore", divide="ignore"):
        denom = (
            float(np.dot(pred_at_x[valid_mask], pred_at_x[valid_mask])) if pred_at_x.size else 0.0
        )
    if denom > 0:
        scale = float(np.dot(y[valid_mask], pred_at_x[valid_mask]) / denom)
        if not np.isnan(scale) and not isclose(scale, 1.0, rel_tol=0.05, abs_tol=1e-3):
            y_range = y_range * scale

    # Plot individual segments so the baseline and active slopes are easier to read
    baseline_color = "#6b6b6b"
    heating_color = "#d62728"
    cooling_color = "#1f77b4"

    def _is_zero(value: float | None) -> bool:
        return value is None or isclose(value, 0.0, abs_tol=1e-6)

    def _plot_segment(
        x_vals: np.ndarray,
        y_vals: np.ndarray,
        *,
        color: str,
        label: str | None,
    ) -> Line2D | None:
        if x_vals.size == 0:
            return None
        (line,) = ax.plot(x_vals, y_vals, color=color, linewidth=2, label=label)
        return line

    # Heating segment (left of heating change point)
    heating_cp = model_result.heating_change_point
    heating_line: Line2D | None = None
    if heating_cp is not None and not _is_zero(model_result.heating_slope):
        mask = x_range <= heating_cp
        heating_line = _plot_segment(
            x_range[mask],
            y_range[mask],
            color=heating_color,
            label="Heating Slope",
        )
    else:
        heating_cp = None

    # Baseline / neutral segment
    neutral_start = heating_cp if heating_cp is not None else x_range[0]
    cooling_cp = model_result.cooling_change_point
    neutral_end = cooling_cp if cooling_cp is not None else x_range[-1]
    baseline_mask = (x_range >= neutral_start) & (x_range <= neutral_end)
    baseline_line = _plot_segment(
        x_range[baseline_mask],
        y_range[baseline_mask],
        color=baseline_color,
        label="Baseload",
    )

    # Cooling segment (right of cooling change point)
    cooling_line: Line2D | None = None
    if cooling_cp is not None and not _is_zero(model_result.cooling_slope):
        mask = x_range >= cooling_cp
        cooling_line = _plot_segment(
            x_range[mask],
            y_range[mask],
            color=cooling_color,
            label="Cooling Slope",
        )

    # Add changepoint markers
    # No explicit changepoint markers; values remain in annotation box

    # Create info text
    model_type_map = {
        "1P": "1-Parameter",
        "3P Heating": "3-Parameter Heating",
        "3P Cooling": "3-Parameter Cooling",
        "5P": "5-Parameter",
    }
    model_label_long = model_type_map.get(model_result.model_type, model_result.model_type)

    info_text = f"Model: {model_label_long}\n"
    info_text += f"R² = {model_result.r_squared:.3f}\n"
    info_text += f"CV-RMSE = {model_result.cvrmse:.3f}\n"
    info_text += f"Baseload = {model_result.baseload:.2f}"

    if model_result.heating_slope is not None:
        info_text += f"\nHeating Slope = {model_result.heating_slope:.3f}"
        if model_result.heating_change_point is not None:
            info_text += f"\nHeating Change-point = {model_result.heating_change_point:.1f}"

    if model_result.cooling_slope is not None:
        info_text += f"\nCooling Slope = {model_result.cooling_slope:.3f}"
        if model_result.cooling_change_point is not None:
            info_text += f"\nCooling Change-point = {model_result.cooling_change_point:.1f}"

    # Add info box outside the plotting area, top-right
    ax.text(
        1.02,
        0.98,
        info_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="left",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
    )

    # Set labels and title
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if title is None:
        title = f"Change-Point Model ({len(x)} data points)"
    ax.set_title(title)
    legend_handles = [scatter]
    legend_labels = ["Data"]
    for line, label in (
        (heating_line, "Heating Slope"),
        (cooling_line, "Cooling Slope"),
        (baseline_line, "Baseload"),
    ):
        if line is not None and label not in legend_labels:
            legend_handles.append(line)
            legend_labels.append(label)

    ax.legend(
        legend_handles,
        legend_labels,
        loc="upper left",
        bbox_to_anchor=(1.02, 0.7),
        borderaxespad=0.0,
        frameon=True,
    )
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig, ax


class ChangePointModelResult(BaseModel):
    """Result of change-point model fitting.

    Contains all coefficients, goodness-of-fit metrics, and metadata
    from fitting a change-point model to energy usage data.
    """

    heating_slope: float | None = Field(None, description="Heating slope coefficient")
    heating_change_point: float | None = Field(None, description="Heating change point temperature")
    baseload: float = Field(..., description="Baseload consumption")
    cooling_change_point: float | None = Field(None, description="Cooling change point temperature")
    cooling_slope: float | None = Field(None, description="Cooling slope coefficient")
    r_squared: float = Field(..., ge=0, le=1, description="R-squared value")
    cvrmse: float = Field(..., ge=0, description="CV(RMSE) value")
    model_type: str = Field(..., description="Model type (1P, 3P Heating, 3P Cooling, 5P)")
    heating_pvalue: float | None = Field(None, description="P-value for heating slope significance")
    cooling_pvalue: float | None = Field(None, description="P-value for cooling slope significance")

    def is_valid(self, min_r_squared: float = 0.6, max_cvrmse: float = 0.5) -> bool:
        """Check if model meets quality thresholds."""
        return self.r_squared >= min_r_squared and self.cvrmse <= max_cvrmse

    def get_model_complexity(self) -> int:
        """Get number of parameters in the model."""
        model_params = {"1P": 1, "3P Heating": 3, "3P Cooling": 3, "5P": 5}
        return model_params.get(self.model_type, 1)

    def estimate_annual_consumption(self, annual_hdd: float, annual_cdd: float) -> float:
        """Estimate annual energy consumption using heating/cooling degree days."""
        annual = self.baseload * 365
        if self.heating_slope:
            annual += self.heating_slope * annual_hdd
        if self.cooling_slope:
            annual += self.cooling_slope * annual_cdd
        return annual
