"""
Weather-related algorithms and calculations.

This module provides pure functions for weather data processing,
temperature conversions, and degree day calculations.
"""

from typing import List, Optional, Union
import numpy as np
import math


def celsius_to_fahrenheit(temp_c: float) -> float:
    """
    Convert temperature from Celsius to Fahrenheit.
    
    Args:
        temp_c: Temperature in Celsius
        
    Returns:
        Temperature in Fahrenheit
    """
    if not isinstance(temp_c, (int, float)) or math.isnan(temp_c):
        return float('nan')
    return temp_c * 1.8 + 32


def fahrenheit_to_celsius(temp_f: float) -> float:
    """
    Convert temperature from Fahrenheit to Celsius.
    
    Args:
        temp_f: Temperature in Fahrenheit
        
    Returns:
        Temperature in Celsius
    """
    if not isinstance(temp_f, (int, float)) or math.isnan(temp_f):
        return float('nan')
    return (temp_f - 32) / 1.8


def convert_temperature(
    temp: float,
    from_unit: str = 'C',
    to_unit: str = 'F'
) -> float:
    """
    Convert temperature between units.
    
    Args:
        temp: Temperature value
        from_unit: Source unit ('C' or 'F')
        to_unit: Target unit ('C' or 'F')
        
    Returns:
        Converted temperature
    """
    if from_unit == to_unit:
        return temp
    
    if from_unit.upper() == 'C' and to_unit.upper() == 'F':
        return celsius_to_fahrenheit(temp)
    elif from_unit.upper() == 'F' and to_unit.upper() == 'C':
        return fahrenheit_to_celsius(temp)
    else:
        raise ValueError(f"Invalid temperature units: from {from_unit} to {to_unit}")


def convert_temperature_list(
    temps: List[float],
    from_unit: str = 'C',
    to_unit: str = 'F'
) -> List[float]:
    """
    Convert a list of temperatures between units.
    
    Args:
        temps: List of temperature values
        from_unit: Source unit ('C' or 'F')
        to_unit: Target unit ('C' or 'F')
        
    Returns:
        List of converted temperatures
    """
    if not temps:
        return []
    return [convert_temperature(t, from_unit, to_unit) for t in temps]


def calculate_heating_degree_days(
    daily_temps: Union[np.ndarray, List[float]],
    base_temp: float = 65.0,
    temp_unit: str = 'F'
) -> float:
    """
    Calculate Heating Degree Days (HDD) for a period.
    
    HDD measures how much (in degrees), and for how long (in days),
    the outside air temperature was below a certain level (base temperature).
    
    Args:
        daily_temps: Array of daily average temperatures
        base_temp: Base temperature for HDD calculation (default 65°F)
        temp_unit: Temperature unit ('F' or 'C')
        
    Returns:
        Total heating degree days
    """
    if not isinstance(daily_temps, np.ndarray):
        daily_temps = np.array(daily_temps)
    
    # Convert base temp to match the unit if needed
    if temp_unit.upper() == 'C' and base_temp == 65.0:
        # Default is in Fahrenheit, convert to Celsius
        base_temp = fahrenheit_to_celsius(base_temp)
    
    # Calculate HDD: sum of (base_temp - daily_temp) for days below base
    hdd = np.maximum(base_temp - daily_temps, 0)
    return float(np.sum(hdd))


def calculate_cooling_degree_days(
    daily_temps: Union[np.ndarray, List[float]],
    base_temp: float = 65.0,
    temp_unit: str = 'F'
) -> float:
    """
    Calculate Cooling Degree Days (CDD) for a period.
    
    CDD measures how much (in degrees), and for how long (in days),
    the outside air temperature was above a certain level (base temperature).
    
    Args:
        daily_temps: Array of daily average temperatures
        base_temp: Base temperature for CDD calculation (default 65°F)
        temp_unit: Temperature unit ('F' or 'C')
        
    Returns:
        Total cooling degree days
    """
    if not isinstance(daily_temps, np.ndarray):
        daily_temps = np.array(daily_temps)
    
    # Convert base temp to match the unit if needed
    if temp_unit.upper() == 'C' and base_temp == 65.0:
        # Default is in Fahrenheit, convert to Celsius
        base_temp = fahrenheit_to_celsius(base_temp)
    
    # Calculate CDD: sum of (daily_temp - base_temp) for days above base
    cdd = np.maximum(daily_temps - base_temp, 0)
    return float(np.sum(cdd))


def calculate_monthly_average(
    hourly_temps: Union[np.ndarray, List[float]]
) -> float:
    """
    Calculate monthly average temperature from hourly data.
    
    Args:
        hourly_temps: Array of hourly temperature readings
        
    Returns:
        Average temperature for the month
    """
    if not hourly_temps:
        return float('nan')
    
    if not isinstance(hourly_temps, np.ndarray):
        hourly_temps = np.array(hourly_temps)
    
    # Filter out NaN values
    valid_temps = hourly_temps[~np.isnan(hourly_temps)]
    
    if len(valid_temps) == 0:
        return float('nan')
    
    return float(np.mean(valid_temps))


def estimate_monthly_hdd(
    avg_temp: float,
    days_in_month: int = 30,
    base_temp: float = 65.0
) -> float:
    """
    Estimate monthly HDD from average temperature.
    
    This is a simplified estimation when daily data is not available.
    
    Args:
        avg_temp: Monthly average temperature
        days_in_month: Number of days in the month
        base_temp: Base temperature for HDD calculation
        
    Returns:
        Estimated heating degree days
    """
    if math.isnan(avg_temp):
        return 0.0
    
    # Simple linear estimation
    if avg_temp >= base_temp:
        return 0.0
    
    return (base_temp - avg_temp) * days_in_month


def estimate_monthly_cdd(
    avg_temp: float,
    days_in_month: int = 30,
    base_temp: float = 65.0
) -> float:
    """
    Estimate monthly CDD from average temperature.
    
    This is a simplified estimation when daily data is not available.
    
    Args:
        avg_temp: Monthly average temperature
        days_in_month: Number of days in the month
        base_temp: Base temperature for CDD calculation
        
    Returns:
        Estimated cooling degree days
    """
    if math.isnan(avg_temp):
        return 0.0
    
    # Simple linear estimation
    if avg_temp <= base_temp:
        return 0.0
    
    return (avg_temp - base_temp) * days_in_month


def validate_temperature_range(
    temp_c: float,
    min_temp_c: float = -60.0,
    max_temp_c: float = 60.0
) -> bool:
    """
    Validate if temperature is within reasonable range.
    
    Args:
        temp_c: Temperature in Celsius
        min_temp_c: Minimum reasonable temperature (default -60°C)
        max_temp_c: Maximum reasonable temperature (default 60°C)
        
    Returns:
        True if temperature is valid, False otherwise
    """
    if math.isnan(temp_c) or math.isinf(temp_c):
        return False
    
    return min_temp_c <= temp_c <= max_temp_c

