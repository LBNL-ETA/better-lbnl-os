"""Weather-related algorithms and calculations (moved).

Pure functions for weather data processing, temperature conversions, and
degree day calculations. Moved from core.weather.calculations.
"""

from typing import List, Optional, Union
import numpy as np
import math


def celsius_to_fahrenheit(temp_c: float) -> float:
    if not isinstance(temp_c, (int, float)) or math.isnan(temp_c):
        return float('nan')
    return temp_c * 1.8 + 32


def fahrenheit_to_celsius(temp_f: float) -> float:
    if not isinstance(temp_f, (int, float)) or math.isnan(temp_f):
        return float('nan')
    return (temp_f - 32) / 1.8


def convert_temperature(temp: float, from_unit: str = 'C', to_unit: str = 'F') -> float:
    if from_unit == to_unit:
        return temp
    if from_unit.upper() == 'C' and to_unit.upper() == 'F':
        return celsius_to_fahrenheit(temp)
    elif from_unit.upper() == 'F' and to_unit.upper() == 'C':
        return fahrenheit_to_celsius(temp)
    else:
        raise ValueError(f"Invalid temperature units: from {from_unit} to {to_unit}")


def convert_temperature_list(temps: List[float], from_unit: str = 'C', to_unit: str = 'F') -> List[float]:
    if not temps:
        return []
    return [convert_temperature(t, from_unit, to_unit) for t in temps]


def calculate_heating_degree_days(
    daily_temps: Union[np.ndarray, List[float]],
    base_temp: float = 65.0,
    temp_unit: str = 'F'
) -> float:
    if not isinstance(daily_temps, np.ndarray):
        daily_temps = np.array(daily_temps)
    if temp_unit.upper() == 'C' and base_temp == 65.0:
        base_temp = fahrenheit_to_celsius(base_temp)
    hdd = np.maximum(base_temp - daily_temps, 0)
    return float(np.sum(hdd))


def calculate_cooling_degree_days(
    daily_temps: Union[np.ndarray, List[float]],
    base_temp: float = 65.0,
    temp_unit: str = 'F'
) -> float:
    if not isinstance(daily_temps, np.ndarray):
        daily_temps = np.array(daily_temps)
    if temp_unit.upper() == 'C' and base_temp == 65.0:
        base_temp = fahrenheit_to_celsius(base_temp)
    cdd = np.maximum(daily_temps - base_temp, 0)
    return float(np.sum(cdd))


def calculate_monthly_average(hourly_temps: Union[np.ndarray, List[float]]) -> float:
    if not hourly_temps:
        return float('nan')
    if not isinstance(hourly_temps, np.ndarray):
        hourly_temps = np.array(hourly_temps)
    valid_temps = hourly_temps[~np.isnan(hourly_temps)]
    if len(valid_temps) == 0:
        return float('nan')
    return float(np.mean(valid_temps))


def estimate_monthly_hdd(avg_temp: float, days_in_month: int = 30, base_temp: float = 65.0) -> float:
    if math.isnan(avg_temp):
        return 0.0
    if avg_temp >= base_temp:
        return 0.0
    return (base_temp - avg_temp) * days_in_month


def estimate_monthly_cdd(avg_temp: float, days_in_month: int = 30, base_temp: float = 65.0) -> float:
    if math.isnan(avg_temp):
        return 0.0
    if avg_temp <= base_temp:
        return 0.0
    return (avg_temp - base_temp) * days_in_month


def validate_temperature_range(temp_c: float, min_temp_c: float = -60.0, max_temp_c: float = 60.0) -> bool:
    if math.isnan(temp_c) or math.isinf(temp_c):
        return False
    return min_temp_c <= temp_c <= max_temp_c

