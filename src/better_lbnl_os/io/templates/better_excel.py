"""Reader for BETTER Excel template (EN/FR/ES)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from better_lbnl_os.constants import normalize_space_type
from better_lbnl_os.constants.energy import normalize_fuel_type, normalize_fuel_unit
from better_lbnl_os.constants.template_parsing import (
    BETTER_BILLS_HEADERS,
    BETTER_META_HEADERS,
    BETTERTemplateConfig,
)
from better_lbnl_os.models import BuildingData, UtilityBillData

from .types import ParsedPortfolio, ParseMessage


@dataclass
class _SheetNames:
    meta: str = "Property Information"
    bills: str = "Utility Data"


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = list(df.columns)
    # Clean column names - strip whitespace and handle unnamed columns
    cleaned_cols = {}
    for col in cols:
        if isinstance(col, str):
            cleaned = col.strip()
            cleaned_cols[cleaned] = col
        else:
            cleaned_cols[str(col)] = col

    for cand in candidates:
        # Direct match
        if cand in cleaned_cols:
            return cleaned_cols[cand]

    # try case-insensitive match
    lower = {c.lower(): c for c in cleaned_cols.keys()}
    for cand in candidates:
        if cand.lower() in lower:
            orig_col = cleaned_cols[lower[cand.lower()]]
            return orig_col
    return None


def _map_columns(
    df: pd.DataFrame,
    spec: dict[str, list[str]],
    sheet: str,
    errors: list[ParseMessage],
    optional_keys: list[str] | None = None,
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    optional = set(optional_keys or [])
    for key, candidates in spec.items():
        col = _find_column(df, candidates)
        if col is None and key not in optional:
            errors.append(
                ParseMessage(
                    severity="error",
                    sheet=sheet,
                    message=f"Missing required column for {key}: one of {candidates}",
                )
            )
        elif col is not None:
            mapping[key] = col
    return mapping


def read_better_excel(file_like, lang: str | None = None) -> ParsedPortfolio:
    """Parse a BETTER Excel template into a ParsedPortfolio.

    Args:
        file_like: Path or file-like object
        lang: Optional language hint (unused for now; mapping is header-driven)
    """
    sn = _SheetNames()
    result = ParsedPortfolio(metadata={"template_type": "better_excel", "lang": lang})
    config = BETTERTemplateConfig()

    try:
        df_meta = pd.read_excel(
            file_like,
            sheet_name=sn.meta,
            skiprows=config.META_SKIP_ROWS,
            usecols=config.META_USE_COLS,
        )
    except Exception as e:
        result.errors.append(
            ParseMessage(severity="error", sheet=sn.meta, message=f"Failed to read sheet: {e}")
        )
        return result

    try:
        df_bills = pd.read_excel(
            file_like,
            sheet_name=sn.bills,
            skiprows=config.BILLS_SKIP_ROWS,
            usecols=config.BILLS_USE_COLS,
            parse_dates=config.BILLS_DATE_COLS,
        )
    except Exception as e:
        result.errors.append(
            ParseMessage(severity="error", sheet=sn.bills, message=f"Failed to read sheet: {e}")
        )
        return result

    # Map columns (no need for retry logic with deterministic skiprows)
    meta_map = _map_columns(df_meta, BETTER_META_HEADERS, sn.meta, result.errors)
    bills_map = _map_columns(
        df_bills,
        BETTER_BILLS_HEADERS,
        sn.bills,
        result.errors,
        optional_keys=["COST"],
    )

    # Check if required columns were found
    if not meta_map or not bills_map:
        return result

    # Drop meta rows missing building ID
    df_meta = df_meta[df_meta[meta_map["BLDG_ID"]].notna()].copy()

    # Build BuildingData list
    buildings: dict[str, BuildingData] = {}
    for _, row in df_meta.iterrows():
        try:
            bldg_id = str(row[meta_map["BLDG_ID"]]).strip()
            name = str(row[meta_map["BLDG_NAME"]]).strip()
            location = str(row[meta_map["LOCATION"]]).strip()
            floor_area = float(row[meta_map["FLOOR_AREA"]])
            space_type_raw = str(row[meta_map["SPACE_TYPE"]]).strip()
            space_type = normalize_space_type(space_type_raw)
            b = BuildingData(
                name=name,
                floor_area=floor_area,
                space_type=space_type,
                location=location,
                climate_zone=None,
            )
            buildings[bldg_id] = b
        except Exception as e:
            result.errors.append(
                ParseMessage(
                    severity="error",
                    sheet=sn.meta,
                    message=f"Invalid building row: {e}",
                )
            )

    # Filter bills: positive consumption and known building IDs
    df_bills = df_bills.copy()
    # Keep only bills for known buildings if any
    if buildings:
        df_bills = df_bills[df_bills[bills_map["BLDG_ID"]].astype(str).isin(list(buildings.keys()))]

    # Only positive consumption
    try:
        df_bills = df_bills[df_bills[bills_map["CONSUMPTION"]] > 0]
    except Exception:
        pass

    # Parse bills
    bills_by_building: dict[str, list[UtilityBillData]] = {}
    for idx, row in df_bills.iterrows():
        try:
            bid = str(row[bills_map["BLDG_ID"]]).strip()
            start_dt = pd.to_datetime(row[bills_map["START"]])
            end_dt = pd.to_datetime(row[bills_map["END"]])
            start = start_dt.date() if hasattr(start_dt, "date") else pd.Timestamp(start_dt).date()
            end = end_dt.date() if hasattr(end_dt, "date") else pd.Timestamp(end_dt).date()
            if end <= start:
                raise ValueError("End date must be after start date")
            fuel = str(row[bills_map["FUEL"]]).strip()
            unit = str(row[bills_map["UNIT"]]).strip()
            fuel = normalize_fuel_type(fuel)
            unit = normalize_fuel_unit(unit)
            # Try mapping PM-like names if present; otherwise preserve
            cons = float(row[bills_map["CONSUMPTION"]])
            cost = None
            if (
                bills_map.get("COST")
                and bills_map["COST"] in df_bills.columns
                and pd.notna(row[bills_map["COST"]])
            ):
                try:
                    cost = float(row[bills_map["COST"]])
                except Exception:
                    cost = None
            ub = UtilityBillData(
                fuel_type=fuel,
                start_date=start,
                end_date=end,
                consumption=cons,
                units=unit,
                cost=cost,
            )
            bills_by_building.setdefault(bid, []).append(ub)
        except Exception as e:
            result.errors.append(
                ParseMessage(
                    severity="error",
                    sheet=sn.bills,
                    row=int(idx) if isinstance(idx, (int, float)) else None,
                    message=f"Invalid bill row: {e}",
                )
            )

    result.buildings = list(buildings.values())
    result.bills_by_building = bills_by_building
    return result
