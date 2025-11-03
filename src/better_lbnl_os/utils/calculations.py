"""Weather-related basic calculations.

Pure functions for weather data processing and temperature conversions.
"""

import math

import numpy as np


def celsius_to_fahrenheit(temp_c: float) -> float:
    """Convert temperature from Celsius to Fahrenheit.

    Args:
        temp_c: Temperature in Celsius

    Returns:
        Temperature in Fahrenheit, or NaN if input is invalid
    """
    if not isinstance(temp_c, (int, float)) or math.isnan(temp_c):
        return float("nan")
    return temp_c * 1.8 + 32


def fahrenheit_to_celsius(temp_f: float) -> float:
    """Convert temperature from Fahrenheit to Celsius.

    Args:
        temp_f: Temperature in Fahrenheit

    Returns:
        Temperature in Celsius, or NaN if input is invalid
    """
    if not isinstance(temp_f, (int, float)) or math.isnan(temp_f):
        return float("nan")
    return (temp_f - 32) / 1.8


def convert_temperature(temp: float, from_unit: str = "C", to_unit: str = "F") -> float:
    """Convert temperature between Celsius and Fahrenheit.

    Args:
        temp: Temperature value to convert
        from_unit: Source unit ('C' or 'F')
        to_unit: Target unit ('C' or 'F')

    Returns:
        Converted temperature value

    Raises:
        ValueError: If invalid unit combination is provided
    """
    if from_unit == to_unit:
        return temp
    if from_unit.upper() == "C" and to_unit.upper() == "F":
        return celsius_to_fahrenheit(temp)
    elif from_unit.upper() == "F" and to_unit.upper() == "C":
        return fahrenheit_to_celsius(temp)
    else:
        raise ValueError(f"Invalid temperature units: from {from_unit} to {to_unit}")


def convert_temperature_list(
    temps: list[float], from_unit: str = "C", to_unit: str = "F"
) -> list[float]:
    """Convert a list of temperatures between Celsius and Fahrenheit.

    Args:
        temps: List of temperature values to convert
        from_unit: Source unit ('C' or 'F')
        to_unit: Target unit ('C' or 'F')

    Returns:
        List of converted temperature values
    """
    if not temps:
        return []
    return [convert_temperature(t, from_unit, to_unit) for t in temps]


def calculate_monthly_average(hourly_temps: np.ndarray | list[float]) -> float:
    """Calculate average temperature from hourly data.

    Args:
        hourly_temps: Array or list of hourly temperature values

    Returns:
        Monthly average temperature, or NaN if no valid data
    """
    if not hourly_temps:
        return float("nan")
    if not isinstance(hourly_temps, np.ndarray):
        hourly_temps = np.array(hourly_temps)
    valid_temps = hourly_temps[~np.isnan(hourly_temps)]
    if len(valid_temps) == 0:
        return float("nan")
    return float(np.mean(valid_temps))


def validate_temperature_range(
    temp_c: float, min_temp_c: float = -60.0, max_temp_c: float = 60.0
) -> bool:
    """Validate that temperature is within acceptable range.

    Args:
        temp_c: Temperature in Celsius to validate
        min_temp_c: Minimum acceptable temperature in Celsius
        max_temp_c: Maximum acceptable temperature in Celsius

    Returns:
        True if temperature is valid and within range, False otherwise
    """
    if math.isnan(temp_c) or math.isinf(temp_c):
        return False
    return min_temp_c <= temp_c <= max_temp_c
