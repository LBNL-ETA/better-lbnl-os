"""Statistical calculation functions for model evaluation."""

import numpy as np


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
        return float('inf')
    
    mean_true = np.mean(y_true)
    if mean_true == 0:
        return float('inf')
    
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
