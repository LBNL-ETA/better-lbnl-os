"""
Change-point model fitting algorithms.

This module contains pure change-point modeling functions extracted from 
the BETTER Django application, without any framework dependencies.
"""
import logging
from math import isclose
from typing import Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import optimize, stats

from better_lbnl.data.models import ChangePointModelResult

logger = logging.getLogger(__name__)

# Default model quality thresholds
DEFAULT_R2_THRESHOLD = 0.6
DEFAULT_CVRMSE_THRESHOLD = 0.5
DEFAULT_SIGNIFICANT_PVAL = 0.1


def fit_changepoint_model(
    temperature: np.ndarray,
    energy_use: np.ndarray,
    min_r_squared: float = DEFAULT_R2_THRESHOLD,
    max_cv_rmse: float = DEFAULT_CVRMSE_THRESHOLD
) -> ChangePointModelResult:
    """
    Fit a change-point model to temperature and energy use data.
    
    This is the main entry point for change-point model fitting. It automatically
    determines the best model type (1P, 3P, or 5P) based on statistical significance
    and model quality metrics.
    
    Args:
        temperature: Array of temperature values (typically in Celsius)
        energy_use: Array of energy use intensity values (kWh/m²/day)
        min_r_squared: Minimum R² threshold for model acceptance
        max_cv_rmse: Maximum CV-RMSE threshold for model acceptance
        
    Returns:
        ChangePointModelResult with fitted coefficients and quality metrics
        
    Raises:
        ValueError: If input arrays are invalid or empty
        Exception: If model fitting fails
    """
    # Input validation
    _validate_model_inputs(temperature, energy_use)
    
    # Set up bounds for model fitting
    bounds = _create_model_bounds(temperature, energy_use)
    
    # Try fitting with different change-point bounds
    search_bounds = _create_changepoint_search_bounds(temperature, n_bins=8)
    fit_results = []
    
    for cp_bounds in search_bounds:
        try:
            # Update bounds for this iteration
            iteration_bounds = bounds.copy()
            iteration_bounds[0][1] = cp_bounds[0][0]  # heating changepoint lower
            iteration_bounds[1][1] = cp_bounds[0][1]  # heating changepoint upper  
            iteration_bounds[0][3] = cp_bounds[1][0]  # cooling changepoint lower
            iteration_bounds[1][3] = cp_bounds[1][1]  # cooling changepoint upper
            
            result = _fit_model_once(temperature, energy_use, iteration_bounds)
            fit_results.append(result)
            
        except Exception:
            # Some bounds combinations may fail - this is expected
            continue
    
    if not fit_results:
        raise Exception("Could not fit any change-point model with given data")
    
    # Select best model and determine type
    optimal_model = _select_optimal_model(
        fit_results, temperature, energy_use, min_r_squared, max_cv_rmse
    )
    
    return optimal_model


def _validate_model_inputs(temperature: np.ndarray, energy_use: np.ndarray) -> None:
    """Validate inputs for change-point model fitting."""
    if not np.any(temperature):
        raise ValueError("Temperature must have at least one element")
    if not np.any(energy_use):
        raise ValueError("Energy use must have at least one element")
    if np.size(energy_use) != np.size(temperature):
        raise ValueError("Temperature and energy use arrays must have the same length")
    if all(np.isnan(temperature)):
        raise ValueError("Temperature data cannot be all NaN")


def _create_model_bounds(temperature: np.ndarray, energy_use: np.ndarray) -> list:
    """Create bounds for model coefficient optimization."""
    hsl_bounds = [-np.inf, 0]  # heating slope (negative)
    hcp_bounds = [np.min(temperature), np.max(temperature)]  # heating changepoint
    base_bounds = [np.min(energy_use), np.max(energy_use)]  # baseload
    ccp_bounds = [np.min(temperature), np.max(temperature)]  # cooling changepoint
    csl_bounds = [0, np.inf]  # cooling slope (positive)
    
    return [
        [hsl_bounds[0], hcp_bounds[0], base_bounds[0], ccp_bounds[0], csl_bounds[0]],
        [hsl_bounds[1], hcp_bounds[1], base_bounds[1], ccp_bounds[1], csl_bounds[1]]
    ]


def _create_changepoint_search_bounds(temperature: np.ndarray, n_bins: int = 4) -> list:
    """Create search bounds for heating and cooling changepoints."""
    bin_width = np.ptp(temperature) / n_bins
    marks = [np.min(temperature) + i * bin_width for i in range(n_bins + 1)]
    
    bounds_list = []
    for i in range(len(marks) - 1):
        for j in range(i + 1, len(marks) - 1):
            bounds_list.append([
                (marks[i], marks[i + 1]),  # heating changepoint bounds
                (marks[j], marks[j + 1])   # cooling changepoint bounds
            ])
    
    return bounds_list


def _fit_model_once(
    temperature: np.ndarray, 
    energy_use: np.ndarray, 
    bounds: list
) -> Dict:
    """Fit the piecewise linear model once with given bounds."""
    # Perform curve fitting
    popt, pcov = optimize.curve_fit(
        f=piecewise_linear_5p,
        xdata=temperature,
        ydata=energy_use,
        bounds=bounds,
        method='dogbox'
    )
    
    # Calculate model quality metrics
    y_predicted = piecewise_linear_5p(temperature, *popt)
    r2 = calculate_r_squared(energy_use, y_predicted)
    cvrmse = calculate_cvrmse(energy_use, y_predicted)
    
    # Check slope significance
    pval_heating, valid_heating = _check_slope_significance(
        popt[0], temperature, energy_use, popt, is_heating=True
    )
    pval_cooling, valid_cooling = _check_slope_significance(
        popt[4], temperature, energy_use, popt, is_heating=False
    )
    
    return {
        "coefficients": popt,
        "covariance": pcov,
        "r_squared": r2,
        "cvrmse": cvrmse,
        "heating_pvalue": pval_heating,
        "cooling_pvalue": pval_cooling,
        "heating_significant": valid_heating,
        "cooling_significant": valid_cooling
    }


def _check_slope_significance(
    slope: float,
    temperature: np.ndarray,
    energy_use: np.ndarray, 
    coefficients: np.ndarray,
    is_heating: bool
) -> Tuple[Optional[float], bool]:
    """Check if a heating or cooling slope is statistically significant."""
    if isclose(slope, 0, abs_tol=1e-5):
        return None, False
    
    if is_heating:
        # Check heating slope significance
        changepoint = coefficients[1]
        mask = temperature <= changepoint
    else:
        # Check cooling slope significance  
        changepoint = coefficients[3]
        mask = temperature >= changepoint
    
    x_subset = temperature[mask]
    y_subset = energy_use[mask]
    
    if len(x_subset) <= 2:
        return np.inf, False
    
    y_predicted = piecewise_linear_5p(x_subset, *coefficients)
    pvalue = _calculate_slope_pvalue(slope, x_subset, y_subset, y_predicted)
    
    return pvalue, pvalue < DEFAULT_SIGNIFICANT_PVAL


def _calculate_slope_pvalue(
    slope: float,
    x_data: np.ndarray,
    y_data: np.ndarray, 
    y_predicted: np.ndarray
) -> float:
    """Calculate p-value for regression slope significance."""
    if len(x_data) <= 2:
        return np.inf
        
    # Calculate standard error of slope
    residuals = y_data - y_predicted
    sample_variance = np.sum(residuals ** 2) / (len(x_data) - 2)
    sum_squares_x = np.sum((x_data - np.mean(x_data)) ** 2)
    standard_error = np.sqrt(sample_variance / sum_squares_x)
    
    # Calculate t-statistic and p-value
    t_statistic = slope / standard_error
    pvalue = stats.t.sf(np.abs(t_statistic), len(x_data) - 1) * 2  # two-tailed test
    
    return pvalue


def _select_optimal_model(
    fit_results: list,
    temperature: np.ndarray,
    energy_use: np.ndarray,
    min_r_squared: float,
    max_cv_rmse: float
) -> ChangePointModelResult:
    """Select the optimal model from fit results and determine model type."""
    # Convert results to DataFrame for easier analysis
    rows = []
    for result in fit_results:
        coeff = result["coefficients"]
        row = [
            coeff[0], coeff[1], coeff[2], coeff[3], coeff[4],  # coefficients
            result["r_squared"], result["cvrmse"],
            result["heating_pvalue"], result["cooling_pvalue"],
            result["heating_significant"], result["cooling_significant"]
        ]
        rows.append(row)
    
    df_fits = pd.DataFrame(rows, columns=[
        'heating_slope', 'heating_changepoint', 'baseload', 'cooling_changepoint', 'cooling_slope',
        'r_squared', 'cvrmse', 'heating_pvalue', 'cooling_pvalue',
        'heating_significant', 'cooling_significant'
    ])
    
    # Filter for models with at least one significant slope
    df_significant = df_fits[
        (df_fits['heating_significant']) | (df_fits['cooling_significant'])
    ]
    
    if len(df_significant) > 0:
        # Select model with highest R²
        best_idx = df_significant['r_squared'].idxmax()
        best_model = df_significant.loc[best_idx]
        
        # Determine model type and validate
        model_type, coefficients = _determine_model_type(best_model, temperature, energy_use, min_r_squared)
        
        if model_type != "No-fit":
            return ChangePointModelResult(
                model_type=model_type,
                heating_slope=coefficients.get('heating_slope'),
                heating_change_point=coefficients.get('heating_changepoint'), 
                baseload=coefficients['baseload'],
                cooling_change_point=coefficients.get('cooling_changepoint'),
                cooling_slope=coefficients.get('cooling_slope'),
                r_squared=best_model['r_squared'],
                cvrmse=best_model['cvrmse'],
                heating_pvalue=best_model['heating_pvalue'],
                cooling_pvalue=best_model['cooling_pvalue']
            )
    
    # Try 1P model as fallback
    return _fit_1p_model(temperature, energy_use, max_cv_rmse)


def _determine_model_type(
    model_row: pd.Series,
    temperature: np.ndarray,
    energy_use: np.ndarray,
    min_r_squared: float
) -> Tuple[str, Dict]:
    """Determine model type (5P, 3P, etc.) and extract coefficients."""
    heating_significant = model_row['heating_significant']
    cooling_significant = model_row['cooling_significant']
    
    if heating_significant and cooling_significant:
        # 5P model
        coefficients = {
            'heating_slope': model_row['heating_slope'],
            'heating_changepoint': model_row['heating_changepoint'],
            'baseload': model_row['baseload'],
            'cooling_changepoint': model_row['cooling_changepoint'],
            'cooling_slope': model_row['cooling_slope']
        }
        
        # Validate R² threshold
        test_coeffs = [
            coefficients['heating_slope'], coefficients['heating_changepoint'],
            coefficients['baseload'], coefficients['cooling_changepoint'], 
            coefficients['cooling_slope']
        ]
        
        if _check_r2_threshold(temperature, energy_use, test_coeffs, min_r_squared):
            return "5P", coefficients
            
    elif cooling_significant and not heating_significant:
        # 3P cooling model
        coefficients = {
            'heating_slope': None,
            'heating_changepoint': None,
            'baseload': model_row['baseload'],
            'cooling_changepoint': model_row['cooling_changepoint'],
            'cooling_slope': model_row['cooling_slope']
        }
        
        test_coeffs = [None, None, coefficients['baseload'], 
                      coefficients['cooling_changepoint'], coefficients['cooling_slope']]
        
        if _check_r2_threshold(temperature, energy_use, test_coeffs, min_r_squared):
            return "3P-C", coefficients
            
    elif heating_significant and not cooling_significant:
        # 3P heating model
        coefficients = {
            'heating_slope': model_row['heating_slope'],
            'heating_changepoint': model_row['heating_changepoint'],
            'baseload': model_row['baseload'],
            'cooling_changepoint': None,
            'cooling_slope': None
        }
        
        test_coeffs = [coefficients['heating_slope'], coefficients['heating_changepoint'],
                      coefficients['baseload'], None, None]
        
        if _check_r2_threshold(temperature, energy_use, test_coeffs, min_r_squared):
            return "3P-H", coefficients
    
    return "No-fit", {}


def _check_r2_threshold(
    temperature: np.ndarray,
    energy_use: np.ndarray,
    coefficients: list,
    min_r_squared: float
) -> bool:
    """Check if model meets R² threshold."""
    predicted = piecewise_linear_5p(temperature, *coefficients)
    r2 = calculate_r_squared(energy_use, predicted)
    return r2 >= min_r_squared


def _fit_1p_model(
    temperature: np.ndarray,
    energy_use: np.ndarray,
    max_cv_rmse: float
) -> ChangePointModelResult:
    """Fit a 1P (constant) model as fallback."""
    baseload = np.mean(energy_use)
    predicted = np.full_like(energy_use, baseload)
    
    r2 = calculate_r_squared(energy_use, predicted)
    cvrmse = calculate_cvrmse(energy_use, predicted)
    
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
        cooling_pvalue=None
    )


def piecewise_linear_5p(
    x: np.ndarray,
    heating_slope: Optional[float],
    heating_changepoint: Optional[float], 
    baseload: float,
    cooling_changepoint: Optional[float],
    cooling_slope: Optional[float]
) -> np.ndarray:
    """
    Five-parameter piecewise linear function for change-point modeling.
    
    This function implements the classic change-point model:
    - Heating slope (negative) below heating changepoint
    - Flat baseload between changepoints  
    - Cooling slope (positive) above cooling changepoint
    
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
    if all(param is None or np.isnan(param) for param in [
        heating_slope, heating_changepoint, cooling_changepoint, cooling_slope
    ]):
        return np.full_like(x, baseload)
    
    # Handle 3P models by setting missing parameters
    if heating_changepoint is None or heating_slope is None or np.isnan(heating_changepoint) or np.isnan(heating_slope):
        heating_changepoint = cooling_changepoint
        heating_slope = 0
        
    if cooling_changepoint is None or cooling_slope is None or np.isnan(cooling_changepoint) or np.isnan(cooling_slope):
        cooling_changepoint = heating_changepoint  
        cooling_slope = 0
    
    # Define conditions and functions for piecewise model
    conditions = [
        x < heating_changepoint,
        (x >= heating_changepoint) & (x <= cooling_changepoint),
        x > cooling_changepoint
    ]
    
    functions = [
        lambda x: heating_slope * x + baseload - heating_slope * heating_changepoint,
        lambda x: baseload,
        lambda x: cooling_slope * x + baseload - cooling_slope * cooling_changepoint
    ]
    
    return np.piecewise(x, conditions, functions)


def calculate_r_squared(y_actual: np.ndarray, y_predicted: Union[np.ndarray, float]) -> float:
    """
    Calculate R-squared (coefficient of determination).
    
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
    ss_residuals = np.sum(residuals ** 2)
    ss_total = np.sum((y_actual - np.mean(y_actual)) ** 2)
    
    if ss_total == 0:
        raise Exception(
            "Cannot calculate R² because there is no variability in the actual values. "
            "Please ensure your data contains varying energy consumption values."
        )
    
    return 1 - (ss_residuals / ss_total)


def calculate_cvrmse(y_actual: np.ndarray, y_predicted: np.ndarray) -> float:
    """
    Calculate Coefficient of Variation of Root Mean Squared Error.
    
    Args:
        y_actual: Actual values
        y_predicted: Predicted values
        
    Returns:
        CV-RMSE value
    """
    rmse = np.sqrt(np.mean((y_actual - y_predicted) ** 2))
    mean_actual = np.mean(y_actual)
    
    return rmse / mean_actual if mean_actual != 0 else np.inf


# Compatibility functions for specific model types
def fit_3p_heating(
    temperature: np.ndarray,
    energy_use: np.ndarray
) -> ChangePointModelResult:
    """Fit 3-parameter heating model."""
    result = fit_changepoint_model(temperature, energy_use)
    # Force to 3P heating if possible
    if result.model_type in ["5P", "3P-H"]:
        return ChangePointModelResult(
            model_type="3P-H",
            heating_slope=result.heating_slope,
            heating_change_point=result.heating_change_point,
            baseload=result.baseload,
            cooling_change_point=None,
            cooling_slope=None,
            r_squared=result.r_squared,
            cvrmse=result.cvrmse
        )
    return result


def fit_3p_cooling(
    temperature: np.ndarray,
    energy_use: np.ndarray
) -> ChangePointModelResult:
    """Fit 3-parameter cooling model."""
    result = fit_changepoint_model(temperature, energy_use)
    # Force to 3P cooling if possible  
    if result.model_type in ["5P", "3P-C"]:
        return ChangePointModelResult(
            model_type="3P-C",
            heating_slope=None,
            heating_change_point=None,
            baseload=result.baseload,
            cooling_change_point=result.cooling_change_point,
            cooling_slope=result.cooling_slope,
            r_squared=result.r_squared,
            cvrmse=result.cvrmse
        )
    return result


def fit_5p_model(
    temperature: np.ndarray,
    energy_use: np.ndarray
) -> ChangePointModelResult:
    """Fit 5-parameter model."""
    return fit_changepoint_model(temperature, energy_use)