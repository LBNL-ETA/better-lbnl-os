"""Fuel and unit normalization plus energy conversion factors."""

from __future__ import annotations

import math
from collections.abc import Mapping
from enum import Enum


class FuelType(str, Enum):
    """Canonical fuel type identifiers used across the OS library."""

    ELECTRIC_GRID = "ELECTRIC_GRID"
    ELECTRIC_SOLAR = "ELECTRIC_SOLAR"
    ELECTRIC_WIND = "ELECTRIC_WIND"
    NATURAL_GAS = "NATURAL_GAS"
    DIESEL = "DIESEL"
    PROPANE = "PROPANE"
    COAL_ANTHRACITE = "COAL_ANTHRACITE"
    COAL_BITUMINOUS = "COAL_BITUMINOUS"
    COKE = "COKE"
    FUEL_OIL_1 = "FUEL_OIL_1"
    FUEL_OIL_2 = "FUEL_OIL_2"
    FUEL_OIL_4 = "FUEL_OIL_4"
    FUEL_OIL_5_AND_6 = "FUEL_OIL_5_AND_6"
    KEROSENE = "KEROSENE"
    WOOD = "WOOD"
    DISTRICT_STEAM = "DISTRICT_STEAM"
    DISTRICT_HOT_WATER = "DISTRICT_HOT_WATER"
    DISTRICT_CHILLED_WATER_ELECTRIC = "DISTRICT_CHILLED_WATER_ELECTRIC"
    DISTRICT_CHILLED_WATER_ABSORPTION = "DISTRICT_CHILLED_WATER_ABSORPTION"
    DISTRICT_CHILLED_WATER_ENGINE = "DISTRICT_CHILLED_WATER_ENGINE"
    DISTRICT_CHILLED_WATER_OTHER = "DISTRICT_CHILLED_WATER_OTHER"


class FuelUnit(str, Enum):
    """Canonical energy/volume/mass unit identifiers."""

    KWH = "KWH"
    MWH = "MWH"
    GJ = "GJ"
    KBTU = "KBTU"
    MBTU = "MBTU"
    DEKATHERM = "DEKATHERM"
    THERMS = "THERMS"
    GALLONS_US = "GALLONS_US"
    GALLONS_UK = "GALLONS_UK"
    LITERS = "LITERS"
    LBS = "LBS"
    KLBS = "KLBS"
    MLBS = "MLBS"
    TONS = "TONS"
    METRIC_TONNES = "METRIC_TONNES"
    KG = "KG"
    TON_HOURS = "TON_HOURS"
    CUBIC_FEET = "CUBIC_FEET"
    HUNDRED_CUBIC_FEET = "HUNDRED_CUBIC_FEET"
    THOUSAND_CUBIC_FEET = "THOUSAND_CUBIC_FEET"
    MILLION_CUBIC_FEET = "MILLION_CUBIC_FEET"
    CUBIC_METERS = "CUBIC_METERS"


# --- Fuel conversion tables -------------------------------------------------

ELECTRICITY_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.MBTU: 293.071,
    FuelUnit.MWH: 1000.0,
}

NATURAL_GAS_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.HUNDRED_CUBIC_FEET: 30.362,
    FuelUnit.CUBIC_FEET: 0.304,
    FuelUnit.CUBIC_METERS: 10.722,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.THOUSAND_CUBIC_FEET: 303.622,
    FuelUnit.MBTU: 293.071,
    FuelUnit.MILLION_CUBIC_FEET: 303621.660,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.THERMS: 29.307,
}

COAL_ANTHRACITE_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.KLBS: 3676.577,
    FuelUnit.LBS: 3.677,
    FuelUnit.MBTU: 293.071,
    FuelUnit.MLBS: 3676576.950,
    FuelUnit.METRIC_TONNES: 8105.865,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.TONS: 7353.154,
}

COAL_BITUMINOUS_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.KLBS: 3653.131,
    FuelUnit.LBS: 3.653,
    FuelUnit.MBTU: 293.071,
    FuelUnit.MLBS: 3653131.262,
    FuelUnit.METRIC_TONNES: 8054.180,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.TONS: 7306.263,
}

COKE_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.KLBS: 3634.082,
    FuelUnit.LBS: 3.634,
    FuelUnit.MBTU: 293.071,
    FuelUnit.MLBS: 3634081.640,
    FuelUnit.METRIC_TONNES: 8012.271,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.TONS: 7268.163,
}

DIESEL_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GALLONS_UK: 48.570,
    FuelUnit.GALLONS_US: 40.444,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.LITERS: 10.684,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.THERMS: 29.307,
    FuelUnit.MBTU: 293.071,
}

PROPANE_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.HUNDRED_CUBIC_FEET: 73.737,
    FuelUnit.CUBIC_FEET: 0.737,
    FuelUnit.GALLONS_UK: 32.146,
    FuelUnit.GALLONS_US: 26.767,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.THOUSAND_CUBIC_FEET: 737.367,
    FuelUnit.LITERS: 7.071,
    FuelUnit.THERMS: 29.307,
    FuelUnit.MBTU: 293.071,
    FuelUnit.DEKATHERM: 293.001,
}

WOOD_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.MBTU: 293.071,
    FuelUnit.METRIC_TONNES: 4647.228,
    FuelUnit.THERMS: 29.307,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.TONS: 5122.883,
}

FUEL_OIL_1_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GALLONS_UK: 48.921,
    FuelUnit.GALLONS_US: 40.737,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.LITERS: 10.762,
    FuelUnit.THERMS: 29.307,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.MBTU: 293.071,
}

FUEL_OIL_2_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GALLONS_UK: 48.570,
    FuelUnit.GALLONS_US: 40.444,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.LITERS: 10.684,
    FuelUnit.THERMS: 29.307,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.MBTU: 293.071,
}

FUEL_OIL_4_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GALLONS_UK: 51.385,
    FuelUnit.GALLONS_US: 42.788,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.LITERS: 11.303,
    FuelUnit.THERMS: 29.307,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.MBTU: 293.071,
}

FUEL_OIL_5_6_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GALLONS_UK: 52.793,
    FuelUnit.GALLONS_US: 43.961,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.LITERS: 11.613,
    FuelUnit.THERMS: 29.307,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.MBTU: 293.071,
}

KEROSENE_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0,
    FuelUnit.MWH: 1000.0,
    FuelUnit.GALLONS_UK: 47.514,
    FuelUnit.GALLONS_US: 39.565,
    FuelUnit.GJ: 277.778,
    FuelUnit.KBTU: 0.293,
    FuelUnit.LITERS: 10.452,
    FuelUnit.DEKATHERM: 293.001,
    FuelUnit.MBTU: 293.071,
}

DISTRICT_STEAM_SOURCE_TO_SITE = 1.2
DISTRICT_HOT_WATER_SOURCE_TO_SITE = 1.2
DISTRICT_CHILLED_WATER_SOURCE_TO_SITE = 1.09

DISTRICT_STEAM_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.MWH: 1000.0 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.DEKATHERM: 293.001 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.GJ: 277.778 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.KBTU: 0.293 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.KG: 0.771 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.KLBS: 349.927 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.LBS: 0.350 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.MBTU: 293.071 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.MLBS: 349926.893 * DISTRICT_STEAM_SOURCE_TO_SITE,
    FuelUnit.THERMS: 29.307 * DISTRICT_STEAM_SOURCE_TO_SITE,
}

DISTRICT_HOT_WATER_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0 * DISTRICT_HOT_WATER_SOURCE_TO_SITE,
    FuelUnit.MWH: 1000.0 * DISTRICT_HOT_WATER_SOURCE_TO_SITE,
    FuelUnit.GJ: 277.778 * DISTRICT_HOT_WATER_SOURCE_TO_SITE,
    FuelUnit.KBTU: 0.293 * DISTRICT_HOT_WATER_SOURCE_TO_SITE,
    FuelUnit.MBTU: 293.071 * DISTRICT_HOT_WATER_SOURCE_TO_SITE,
    FuelUnit.DEKATHERM: 293.001 * DISTRICT_HOT_WATER_SOURCE_TO_SITE,
    FuelUnit.THERMS: 29.307 * DISTRICT_HOT_WATER_SOURCE_TO_SITE,
}

DISTRICT_CHILLED_WATER_TO_KWH: dict[FuelUnit, float] = {
    FuelUnit.KWH: 1.0 * DISTRICT_CHILLED_WATER_SOURCE_TO_SITE,
    FuelUnit.MWH: 1000.0 * DISTRICT_CHILLED_WATER_SOURCE_TO_SITE,
    FuelUnit.GJ: 277.778 * DISTRICT_CHILLED_WATER_SOURCE_TO_SITE,
    FuelUnit.KBTU: 0.293 * DISTRICT_CHILLED_WATER_SOURCE_TO_SITE,
    FuelUnit.MBTU: 293.071 * DISTRICT_CHILLED_WATER_SOURCE_TO_SITE,
    FuelUnit.THERMS: 29.307 * DISTRICT_CHILLED_WATER_SOURCE_TO_SITE,
    FuelUnit.DEKATHERM: 293.001 * DISTRICT_CHILLED_WATER_SOURCE_TO_SITE,
    FuelUnit.TON_HOURS: 3.517 * DISTRICT_CHILLED_WATER_SOURCE_TO_SITE,
}

CONVERSION_TABLES: dict[FuelType, dict[FuelUnit, float]] = {
    FuelType.ELECTRIC_GRID: ELECTRICITY_TO_KWH,
    FuelType.ELECTRIC_SOLAR: ELECTRICITY_TO_KWH,
    FuelType.ELECTRIC_WIND: ELECTRICITY_TO_KWH,
    FuelType.NATURAL_GAS: NATURAL_GAS_TO_KWH,
    FuelType.DIESEL: DIESEL_TO_KWH,
    FuelType.PROPANE: PROPANE_TO_KWH,
    FuelType.COAL_ANTHRACITE: COAL_ANTHRACITE_TO_KWH,
    FuelType.COAL_BITUMINOUS: COAL_BITUMINOUS_TO_KWH,
    FuelType.COKE: COKE_TO_KWH,
    FuelType.FUEL_OIL_1: FUEL_OIL_1_TO_KWH,
    FuelType.FUEL_OIL_2: FUEL_OIL_2_TO_KWH,
    FuelType.FUEL_OIL_4: FUEL_OIL_4_TO_KWH,
    FuelType.FUEL_OIL_5_AND_6: FUEL_OIL_5_6_TO_KWH,
    FuelType.KEROSENE: KEROSENE_TO_KWH,
    FuelType.WOOD: WOOD_TO_KWH,
    FuelType.DISTRICT_STEAM: DISTRICT_STEAM_TO_KWH,
    FuelType.DISTRICT_HOT_WATER: DISTRICT_HOT_WATER_TO_KWH,
    FuelType.DISTRICT_CHILLED_WATER_ELECTRIC: DISTRICT_CHILLED_WATER_TO_KWH,
    FuelType.DISTRICT_CHILLED_WATER_ABSORPTION: DISTRICT_CHILLED_WATER_TO_KWH,
    FuelType.DISTRICT_CHILLED_WATER_ENGINE: DISTRICT_CHILLED_WATER_TO_KWH,
    FuelType.DISTRICT_CHILLED_WATER_OTHER: DISTRICT_CHILLED_WATER_TO_KWH,
}


def _flatten_conversion_tables(
    tables: Mapping[FuelType, Mapping[FuelUnit, float]],
) -> dict[tuple[str, str], float]:
    output: dict[tuple[str, str], float] = {}
    for fuel, unit_map in tables.items():
        for unit, factor in unit_map.items():
            output[(fuel.value, unit.value)] = float(factor)
    return output


CONVERSION_TO_KWH: dict[tuple[str, str], float] = _flatten_conversion_tables(CONVERSION_TABLES)


# --- Alias dictionaries -----------------------------------------------------

_FUEL_TYPE_ALIAS_MAP: dict[str, FuelType] = {
    "electric": FuelType.ELECTRIC_GRID,
    "electricity": FuelType.ELECTRIC_GRID,
    "electric - grid": FuelType.ELECTRIC_GRID,
    "electric grid": FuelType.ELECTRIC_GRID,
    "electricidad de red": FuelType.ELECTRIC_GRID,
    "electricite - reseau": FuelType.ELECTRIC_GRID,
    "electric - solar": FuelType.ELECTRIC_SOLAR,
    "electric solar": FuelType.ELECTRIC_SOLAR,
    "electricidad solar": FuelType.ELECTRIC_SOLAR,
    "electricite solaire": FuelType.ELECTRIC_SOLAR,
    "electric - wind": FuelType.ELECTRIC_WIND,
    "electric wind": FuelType.ELECTRIC_WIND,
    "electricidad eolica": FuelType.ELECTRIC_WIND,
    "electricite eolienne": FuelType.ELECTRIC_WIND,
    "natural gas": FuelType.NATURAL_GAS,
    "gas natural": FuelType.NATURAL_GAS,
    "gaz naturel": FuelType.NATURAL_GAS,
    "diesel": FuelType.DIESEL,
    "gasoleo": FuelType.DIESEL,
    "gasoil": FuelType.DIESEL,
    "propane": FuelType.PROPANE,
    "propano": FuelType.PROPANE,
    "coal": FuelType.COAL_BITUMINOUS,
    "coal (anthracite)": FuelType.COAL_ANTHRACITE,
    "coal (bituminous)": FuelType.COAL_BITUMINOUS,
    "charbon (anthracite)": FuelType.COAL_ANTHRACITE,
    "charbon (bitumineux)": FuelType.COAL_BITUMINOUS,
    "carbon antracita": FuelType.COAL_ANTHRACITE,
    "carbon bituminoso": FuelType.COAL_BITUMINOUS,
    "coke": FuelType.COKE,
    "coque": FuelType.COKE,
    "fuel oil": FuelType.FUEL_OIL_2,
    "fuel oil (no. 1)": FuelType.FUEL_OIL_1,
    "fuel oil (no. 2)": FuelType.FUEL_OIL_2,
    "fuel oil (no. 4)": FuelType.FUEL_OIL_4,
    "fuel oil (no. 5)": FuelType.FUEL_OIL_5_AND_6,
    "fuel oil (no. 5 and no. 6)": FuelType.FUEL_OIL_5_AND_6,
    "fuel oil (no. 6)": FuelType.FUEL_OIL_5_AND_6,
    "combustible": FuelType.FUEL_OIL_2,
    "combustoleo (no. 1)": FuelType.FUEL_OIL_1,
    "combustoleo (no. 2)": FuelType.FUEL_OIL_2,
    "combustoleo (no. 4)": FuelType.FUEL_OIL_4,
    "combustoleo (no. 5 y no. 6)": FuelType.FUEL_OIL_5_AND_6,
    "combustoleo": FuelType.FUEL_OIL_2,
    "mazout": FuelType.FUEL_OIL_2,
    "district steam": FuelType.DISTRICT_STEAM,
    "vapor de distrito": FuelType.DISTRICT_STEAM,
    "vapeur de reseau": FuelType.DISTRICT_STEAM,
    "district hot water": FuelType.DISTRICT_HOT_WATER,
    "agua caliente de distrito": FuelType.DISTRICT_HOT_WATER,
    "eau chaude de reseau": FuelType.DISTRICT_HOT_WATER,
    "district chilled water": FuelType.DISTRICT_CHILLED_WATER_OTHER,
    "district chilled water - electric": FuelType.DISTRICT_CHILLED_WATER_ELECTRIC,
    "district chilled water - absorption": FuelType.DISTRICT_CHILLED_WATER_ABSORPTION,
    "district chilled water - engine": FuelType.DISTRICT_CHILLED_WATER_ENGINE,
    "district chilled water - other": FuelType.DISTRICT_CHILLED_WATER_OTHER,
    "agua refrigerada de distrito": FuelType.DISTRICT_CHILLED_WATER_OTHER,
    "agua fria de distrito": FuelType.DISTRICT_CHILLED_WATER_OTHER,
    "agua fria de distrito - electrica": FuelType.DISTRICT_CHILLED_WATER_ELECTRIC,
    "agua refrigerada de distrito - absorcion": FuelType.DISTRICT_CHILLED_WATER_ABSORPTION,
    "agua refrigerada de distrito - motor": FuelType.DISTRICT_CHILLED_WATER_ENGINE,
    "eau refroidie de reseau": FuelType.DISTRICT_CHILLED_WATER_OTHER,
    "eau glacee de reseau": FuelType.DISTRICT_CHILLED_WATER_OTHER,
    "kerosene": FuelType.KEROSENE,
    "queroseno": FuelType.KEROSENE,
    "wood": FuelType.WOOD,
    "madera": FuelType.WOOD,
    "bois": FuelType.WOOD,
}


_UNIT_ALIAS_MAP: dict[str, FuelUnit] = {
    "kwh": FuelUnit.KWH,
    "kwh (thousand watt-hours)": FuelUnit.KWH,
    "mwh": FuelUnit.MWH,
    "mwh (million watt-hours)": FuelUnit.MWH,
    "gj": FuelUnit.GJ,
    "gj (billion joules)": FuelUnit.GJ,
    "kbtu": FuelUnit.KBTU,
    "kbtu (thousand btu)": FuelUnit.KBTU,
    "mbtu": FuelUnit.MBTU,
    "mbtu/mmbtu (million btu)": FuelUnit.MBTU,
    "dekatherm": FuelUnit.DEKATHERM,
    "mbtu/ mmbtu/ dth (million btu/ dekatherm)": FuelUnit.DEKATHERM,
    "therms": FuelUnit.THERMS,
    "gallons (us)": FuelUnit.GALLONS_US,
    "gallons (uk)": FuelUnit.GALLONS_UK,
    "gallons": FuelUnit.GALLONS_US,
    "liters": FuelUnit.LITERS,
    "litres": FuelUnit.LITERS,
    "liters (l)": FuelUnit.LITERS,
    "lbs": FuelUnit.LBS,
    "klbs": FuelUnit.KLBS,
    "klbs (thousand pounds)": FuelUnit.KLBS,
    "mlbs": FuelUnit.MLBS,
    "mlbs (million pounds)": FuelUnit.MLBS,
    "tons": FuelUnit.TONS,
    "metric tonnes": FuelUnit.METRIC_TONNES,
    "kg": FuelUnit.KG,
    "kilograms": FuelUnit.KG,
    "ton hours": FuelUnit.TON_HOURS,
    "ton-hours": FuelUnit.TON_HOURS,
    "ton-hour": FuelUnit.TON_HOURS,
    "cf (cubic feet)": FuelUnit.CUBIC_FEET,
    "cubic feet": FuelUnit.CUBIC_FEET,
    "ccf (hundred cubic feet)": FuelUnit.HUNDRED_CUBIC_FEET,
    "hundred cubic feet": FuelUnit.HUNDRED_CUBIC_FEET,
    "kcf (thousand cubic feet)": FuelUnit.THOUSAND_CUBIC_FEET,
    "thousand cubic feet": FuelUnit.THOUSAND_CUBIC_FEET,
    "mcf (million cubic feet)": FuelUnit.MILLION_CUBIC_FEET,
    "million cubic feet": FuelUnit.MILLION_CUBIC_FEET,
    "cm (cubic meters)": FuelUnit.CUBIC_METERS,
    "cubic meters": FuelUnit.CUBIC_METERS,
    "metros cubicos": FuelUnit.CUBIC_METERS,
    "metres cubes": FuelUnit.CUBIC_METERS,
    "gal": FuelUnit.GALLONS_US,
    "gal (us)": FuelUnit.GALLONS_US,
    "gal (uk)": FuelUnit.GALLONS_UK,
}


def normalize_fuel_type(value: str | None) -> str | None:
    """Return canonical FuelType token for free-form input strings."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    candidate = value.strip() if isinstance(value, str) else str(value).strip()
    if not candidate:
        return candidate

    if candidate in FuelType._value2member_map_:
        return candidate

    upper_candidate = candidate.upper().replace(" ", "_")
    if upper_candidate in FuelType.__members__:
        return FuelType[upper_candidate].value

    alias = _FUEL_TYPE_ALIAS_MAP.get(candidate.lower())
    if alias:
        return alias.value

    return candidate


def normalize_fuel_unit(value: str | None) -> str | None:
    """Return canonical FuelUnit token for free-form unit strings."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    candidate = value.strip() if isinstance(value, str) else str(value).strip()
    if not candidate:
        return candidate

    if candidate in FuelUnit._value2member_map_:
        return candidate

    upper_candidate = candidate.upper().replace(" ", "_")
    if upper_candidate in FuelUnit.__members__:
        return FuelUnit[upper_candidate].value

    alias = _UNIT_ALIAS_MAP.get(candidate.lower())
    if alias:
        return alias.value

    return candidate


def get_conversion_factor(fuel_type: str, unit: str) -> float | None:
    """Lookup the kWh conversion factor for a (fuel, unit) pair."""
    canonical_fuel = normalize_fuel_type(fuel_type)
    canonical_unit = normalize_fuel_unit(unit)
    if canonical_fuel is None or canonical_unit is None:
        return None
    return CONVERSION_TO_KWH.get((canonical_fuel, canonical_unit))


__all__ = [
    "CONVERSION_TABLES",
    "CONVERSION_TO_KWH",
    "FuelType",
    "FuelUnit",
    "get_conversion_factor",
    "normalize_fuel_type",
    "normalize_fuel_unit",
]
