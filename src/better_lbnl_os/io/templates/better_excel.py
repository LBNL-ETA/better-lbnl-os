"""Reader for BETTER Excel template (EN/FR/ES)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from better_lbnl_os.constants import normalize_space_type
from better_lbnl_os.constants.template_parsing import (
    BETTER_META_HEADERS,
    BETTER_BILLS_HEADERS,
    FUEL_NAME_MAP,
    UNIT_NAME_MAP,
)
from better_lbnl_os.models import BuildingData, UtilityBillData
from .types import ParsedPortfolio, ParseMessage


@dataclass
class _SheetNames:
    meta: str = "Property Information"
    bills: str = "Utility Data"


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols = list(df.columns)
    for cand in candidates:
        if cand in cols:
            return cand
    # try case-insensitive match
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def _map_columns(df: pd.DataFrame, spec: Dict[str, List[str]], sheet: str, errors: List[ParseMessage]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for key, candidates in spec.items():
        col = _find_column(df, candidates)
        if col is None:
            errors.append(ParseMessage(
                severity="error",
                sheet=sheet,
                message=f"Missing required column for {key}: one of {candidates}",
            ))
        else:
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

    # Read sheets
    try:
        df_meta = pd.read_excel(file_like, sheet_name=sn.meta)
    except Exception as e:
        result.errors.append(ParseMessage(severity="error", sheet=sn.meta, message=f"Failed to read sheet: {e}"))
        return result

    try:
        df_bills = pd.read_excel(file_like, sheet_name=sn.bills)
    except Exception as e:
        result.errors.append(ParseMessage(severity="error", sheet=sn.bills, message=f"Failed to read sheet: {e}"))
        return result

    # Map columns
    meta_map = _map_columns(df_meta, BETTER_META_HEADERS, sn.meta, result.errors)
    bills_map = _map_columns(df_bills, BETTER_BILLS_HEADERS, sn.bills, result.errors)
    if any(m not in meta_map for m in BETTER_META_HEADERS) or any(m not in bills_map for m in BETTER_BILLS_HEADERS):
        return result

    # Drop meta rows missing building ID
    df_meta = df_meta[df_meta[meta_map["BLDG_ID"]].notna()].copy()

    # Build BuildingData list
    buildings: Dict[str, BuildingData] = {}
    for _, row in df_meta.iterrows():
        try:
            bldg_id = str(row[meta_map["BLDG_ID"]]).strip()
            name = str(row[meta_map["BLDG_NAME"]]).strip()
            location = str(row[meta_map["LOCATION"]]).strip()
            floor_area = float(row[meta_map["FLOOR_AREA"]])
            space_type_raw = str(row[meta_map["SPACE_TYPE"]]).strip()
            space_type = normalize_space_type(space_type_raw)
            b = BuildingData(name=name, floor_area=floor_area, space_type=space_type, location=location)
            buildings[bldg_id] = b
        except Exception as e:
            result.errors.append(ParseMessage(
                severity="error", sheet=sn.meta, message=f"Invalid building row: {e}",
            ))

    # Filter bills: positive consumption and known building IDs
    df_bills = df_bills.copy()
    # Keep only bills for known buildings if any
    if buildings:
        df_bills = df_bills[df_bills[bills_map["BLDG_ID"]].astype(str).isin(buildings.keys())]

    # Only positive consumption
    try:
        df_bills = df_bills[df_bills[bills_map["CONSUMPTION"]] > 0]
    except Exception:
        pass

    # Parse bills
    bills_by_building: Dict[str, List[UtilityBillData]] = {}
    for idx, row in df_bills.iterrows():
        try:
            bid = str(row[bills_map["BLDG_ID"]]).strip()
            start = pd.to_datetime(row[bills_map["START"]]).date()
            end = pd.to_datetime(row[bills_map["END"]]).date()
            if end <= start:
                raise ValueError("End date must be after start date")
            fuel = str(row[bills_map["FUEL"]]).strip()
            unit = str(row[bills_map["UNIT"]]).strip()
            # Try mapping PM-like names if present; otherwise preserve
            fuel = FUEL_NAME_MAP.get(fuel, fuel)
            unit = UNIT_NAME_MAP.get(unit, unit)
            cons = float(row[bills_map["CONSUMPTION"]])
            cost = None
            if bills_map.get("COST") in row and pd.notna(row[bills_map["COST"]]):
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
            result.errors.append(ParseMessage(
                severity="error",
                sheet=sn.bills,
                row=int(idx) if isinstance(idx, (int, float)) else None,
                message=f"Invalid bill row: {e}",
            ))

    result.buildings = list(buildings.values())
    result.bills_by_building = bills_by_building
    return result

