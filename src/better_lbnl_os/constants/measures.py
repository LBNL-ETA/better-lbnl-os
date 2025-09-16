"""Top-level energy efficiency measure definitions."""

from __future__ import annotations

# Canonical list of BETTER's 15 high-level EE measures.
# The tokens match the legacy Django EEMeasures enum so that
# downstream adapters can map back to database records or localized labels.
TOP_LEVEL_EE_MEASURES = {
    "REDUCE_EQUIPMENT_SCHEDULES": "Reduce Equipment Schedules",
    "REDUCE_LIGHTING_LOAD": "Reduce Lighting Load",
    "REDUCE_PLUG_LOADS": "Reduce Plug Loads",
    "INCREASE_COOLING_SYSTEM_EFFICIENCY": "Increase Cooling System Efficiency",
    "DECREASE_HEATING_SETPOINTS": "Decrease Heating Setpoints",
    "ENSURE_ADEQUATE_VENTILATION_RATE": "Ensure Adequate Ventilation Rate",
    "DECREASE_INFILTRATION": "Decrease Infiltration",
    "INCREASE_HEATING_SYSTEM_EFFICIENCY": "Increase Heating System Efficiency",
    "ADD_WALL_CEILING_ROOF_INSULATION": "Add Wall/Ceiling/Roof Insulation",
    "UPGRADE_TO_SUSTAINABLE_RESOURCES_FOR_WATER_HEATING": "Upgrade to Sustainable Resources for Water Heating",
    "UPGRADE_WINDOWS_TO_REDUCE_SOLAR_HEAT_GAIN": "Upgrade Windows to Reduce Solar Heat Gain",
    "USE_HIGH_EFFICIENCY_HEAT_PUMP_FOR_HEATING": "Use High Efficiency Heat Pump for Heating",
    "INCREASE_COOLING_SETPOINTS": "Increase Cooling Setpoints",
    "ADD_FIX_ECONOMIZERS": "Add/Fix Economizers",
    "UPGRADE_WINDOWS_TO_IMPROVE_THERMAL_EFFICIENCY": "Upgrade Windows to Improve Thermal Efficiency",
}

__all__ = ["TOP_LEVEL_EE_MEASURES"]
