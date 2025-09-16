"""Recommendation-specific constant definitions."""

from __future__ import annotations

# Coefficients inspected when generating inefficiency symptoms
SYMPTOM_COEFFICIENTS = (
    "heating_slope",
    "heating_change_point",
    "baseload",
    "cooling_change_point",
    "cooling_slope",
)

# Human-readable descriptions keyed by legacy symptom identifiers
SYMPTOM_DESCRIPTIONS = {
    "low_cooling_change_point": "Cooling turns on earlier than the target change-point.",
    "high_heating_change_point": "Heating change-point is higher than the target value.",
    "high_electricity_baseload": "Electricity baseload exceeds the target level.",
    "high_cooling_sensitivity": "Cooling usage increases faster than targeted with temperature.",
    "high_heating_sensitivity": "Heating usage increases faster than targeted in cold weather.",
    "high_electricity_heating_change_point": "Electric heating change-point is above target.",
    "high_electricity_cooling_sensitivity": "Electric cooling slope is above target.",
    "high_electricity_heating_sensitivity": "Electric heating slope is more negative than target.",
    "high_fossil_fuel_baseload": "Fossil fuel baseload exceeds target.",
}

__all__ = [
    "SYMPTOM_COEFFICIENTS",
    "SYMPTOM_DESCRIPTIONS",
]
