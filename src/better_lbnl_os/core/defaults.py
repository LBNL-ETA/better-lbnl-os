"""Default lookup helpers for fuel prices and emission factors."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources

import pandas as pd

US_STATE_ABBREVIATIONS = {
    "AL": "ALABAMA",
    "AK": "ALASKA",
    "AZ": "ARIZONA",
    "AR": "ARKANSAS",
    "CA": "CALIFORNIA",
    "CO": "COLORADO",
    "CT": "CONNECTICUT",
    "DE": "DELAWARE",
    "FL": "FLORIDA",
    "GA": "GEORGIA",
    "HI": "HAWAII",
    "ID": "IDAHO",
    "IL": "ILLINOIS",
    "IN": "INDIANA",
    "IA": "IOWA",
    "KS": "KANSAS",
    "KY": "KENTUCKY",
    "LA": "LOUISIANA",
    "ME": "MAINE",
    "MD": "MARYLAND",
    "MA": "MASSACHUSETTS",
    "MI": "MICHIGAN",
    "MN": "MINNESOTA",
    "MS": "MISSISSIPPI",
    "MO": "MISSOURI",
    "MT": "MONTANA",
    "NE": "NEBRASKA",
    "NV": "NEVADA",
    "NH": "NEW HAMPSHIRE",
    "NJ": "NEW JERSEY",
    "NM": "NEW MEXICO",
    "NY": "NEW YORK",
    "NC": "NORTH CAROLINA",
    "ND": "NORTH DAKOTA",
    "OH": "OHIO",
    "OK": "OKLAHOMA",
    "OR": "OREGON",
    "PA": "PENNSYLVANIA",
    "RI": "RHODE ISLAND",
    "SC": "SOUTH CAROLINA",
    "SD": "SOUTH DAKOTA",
    "TN": "TENNESSEE",
    "TX": "TEXAS",
    "UT": "UTAH",
    "VT": "VERMONT",
    "VA": "VIRGINIA",
    "WA": "WASHINGTON",
    "WV": "WEST VIRGINIA",
    "WI": "WISCONSIN",
    "WY": "WYOMING",
}

ENERGY_TYPE_TO_PRICE_COLUMN = {
    "ELECTRICITY": "Electricity",
    "FOSSIL_FUEL": "Natural Gas",
}

FOSSIL_DEFAULT_FUEL = {
    "FOSSIL_FUEL": "NATURAL_GAS",
}


@lru_cache
def _load_fuel_price_table() -> pd.DataFrame:
    with (
        resources.files("better_lbnl_os.data.defaults")
        .joinpath("US_fuel_price_2024.csv")
        .open("rb") as fp
    ):
        df = pd.read_csv(fp)
    df["States"] = df["States"].str.upper()
    return df.set_index("States")


@lru_cache
def _load_zip_region_map() -> dict[str, str]:
    with (
        resources.files("better_lbnl_os.data.defaults")
        .joinpath("zip_region_map.csv")
        .open("rb") as fp
    ):
        df = pd.read_csv(fp, dtype={"str_ZIP": str})
    df["zipcode"] = df["str_ZIP"].str.zfill(5)
    return dict(zip(df["zipcode"], df["eGRID_Subregion_1"], strict=False))


@lru_cache
def _load_egrid_factors() -> dict[str, dict[str, float]]:
    with (
        resources.files("better_lbnl_os.data.defaults")
        .joinpath("egrid_emission_factors_2024.json")
        .open("r", encoding="utf-8") as fp
    ):
        return json.load(fp)


@lru_cache
def _load_fossil_factors() -> dict[str, dict[str, dict[str, float]]]:
    with (
        resources.files("better_lbnl_os.data.defaults")
        .joinpath("fossil_emission_factors_2024.json")
        .open("r", encoding="utf-8") as fp
    ):
        return json.load(fp)


def normalize_state_code(value: str | None) -> str | None:
    """Normalize state code to standard 2-letter abbreviation.

    Args:
        value: State name or abbreviation

    Returns:
        Normalized 2-letter state code, or None if invalid
    """
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) == 2 and value.isalpha():
        return value.upper()
    upper = value.upper()
    for abbr, name in US_STATE_ABBREVIATIONS.items():
        if upper == name:
            return abbr
    return None


def infer_state_from_address(address: str | None) -> str | None:
    """Infer state code from address string.

    Args:
        address: Address string to parse

    Returns:
        Inferred 2-letter state code, or None if not found
    """
    if not address:
        return None
    parts = [part.strip() for part in address.split(",") if part.strip()]
    if len(parts) >= 2:
        candidate = parts[-1]
        if len(candidate) == 2 and candidate.isalpha():
            return candidate.upper()
    match = re.search(r"\b([A-Z]{2})\b", address.upper())
    if match:
        return match.group(1)
    return None


def get_default_fuel_price(
    energy_type: str, state: str | None, country_code: str | None
) -> float | None:
    """Get default fuel price for energy type and location.

    Args:
        energy_type: Type of energy (e.g., 'ELECTRICITY', 'NATURAL_GAS')
        state: US state code
        country_code: ISO country code

    Returns:
        Default fuel price, or None if not available
    """
    column = ENERGY_TYPE_TO_PRICE_COLUMN.get(energy_type)
    if column is None:
        return None
    table = _load_fuel_price_table()
    if state and state in table.index:
        value = table.at[state, column]
        if pd.notnull(value):
            return float(value)
    if country_code and country_code.upper() != "US":
        if "INT" in table.index:
            value = table.at["INT", column]
            if pd.notnull(value):
                return float(value)
    return None


def lookup_egrid_subregion(zipcode: str | None) -> str | None:
    """Look up eGRID subregion for a given ZIP code.

    Args:
        zipcode: US ZIP code

    Returns:
        eGRID subregion code, or None if not found
    """
    if not zipcode:
        return None
    zip_clean = re.sub(r"[^0-9]", "", str(zipcode))
    if len(zip_clean) >= 5:
        zip_clean = zip_clean[:5]
        return _load_zip_region_map().get(zip_clean)
    return None


def get_electric_emission_factor(
    region: str | None, country_code: str | None
) -> dict[str, float] | None:
    """Get electric emission factors for a region.

    Args:
        region: eGRID subregion code
        country_code: ISO country code

    Returns:
        Dictionary of emission factors, or None if not available
    """
    factors = _load_egrid_factors()
    if region and region in factors:
        return factors[region]
    if country_code and country_code.upper() in factors:
        return factors[country_code.upper()]
    return factors.get("DEFAULT")


def get_fossil_emission_factor(
    fuel_token: str,
    region_group: str = "OTHERS",
) -> dict[str, float] | None:
    """Get fossil fuel emission factors for a region.

    Args:
        fuel_token: Fuel type identifier
        region_group: Regional grouping code

    Returns:
        Dictionary of emission factors, or None if not available
    """
    groups = _load_fossil_factors()
    group = groups.get(region_group) or groups.get("OTHERS")
    if not group:
        return None
    return group.get(fuel_token)
