"""Reader for Energy Star Portfolio Manager custom download format."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
from pandas.tseries.offsets import MonthEnd

from better_lbnl_os.constants import normalize_space_type, SQFT_TO_SQM
from better_lbnl_os.constants.template_parsing import (
    PM_META_HEADERS as M,
    PM_BILLS_HEADERS as B,
    FUEL_NAME_MAP,
    UNIT_NAME_MAP,
)
from better_lbnl_os.models import BuildingData, UtilityBillData
from .types import ParsedPortfolio, ParseMessage


def read_portfolio_manager(file_like) -> ParsedPortfolio:
    """Parse a Portfolio Manager custom download workbook into a ParsedPortfolio."""
    result = ParsedPortfolio(metadata={"template_type": "portfolio_manager", "unit_system": "IP"})

    # Properties sheet
    try:
        df_meta = pd.read_excel(file_like, sheet_name="Properties")
    except Exception as e:
        result.errors.append(ParseMessage(severity="error", sheet="Properties", message=f"Failed to read sheet: {e}"))
        return result

    # Validate required columns
    missing = [v for v in M.values() if v not in df_meta.columns]
    if missing:
        result.errors.append(ParseMessage(severity="error", sheet="Properties", message=f"Missing columns: {missing}"))
        return result

    # Filter rows with PM ID
    df_meta = df_meta[df_meta[M["PM_ID"]].notna()].copy()

    # Build BuildingData; convert floor area to SI if units are Sq. Ft.
    buildings: Dict[str, BuildingData] = {}
    for _, row in df_meta.iterrows():
        try:
            pmid = str(row[M["PM_ID"]]).strip()
            name = str(row[M["PROP_NAME"]]).strip()
            loc = f"{row[M['CITY']]} , {row[M['STATE']]} {row[M['POSTAL']]}".strip()
            gfa_units = str(row[M["GFA_UNITS"]]).strip()
            gfa = float(row[M["GFA"]])
            if gfa_units.lower().startswith("sq"):
                gfa *= SQFT_TO_SQM
            space_type_raw = str(row[M["SPACE_TYPE"]]).strip()
            space_type = normalize_space_type(space_type_raw)
            b = BuildingData(name=name, floor_area=gfa, space_type=space_type, location=loc)
            buildings[pmid] = b
        except Exception as e:
            result.errors.append(ParseMessage(severity="error", sheet="Properties", message=f"Invalid building row: {e}"))

    # Meter Entries sheet
    try:
        df_bills = pd.read_excel(file_like, sheet_name="Meter Entries")
    except Exception as e:
        result.errors.append(ParseMessage(severity="error", sheet="Meter Entries", message=f"Failed to read sheet: {e}"))
        return result

    missing_b = [v for v in B.values() if v not in df_bills.columns]
    if missing_b:
        result.errors.append(ParseMessage(severity="error", sheet="Meter Entries", message=f"Missing columns: {missing_b}"))
        return result

    # Keep only positive usage
    try:
        df_bills = df_bills[df_bills[B["USAGE_QTY"]] > 0]
    except Exception:
        pass

    # Keep only rows for known PM IDs (if any)
    if buildings:
        df_bills = df_bills[df_bills[B["PM_ID"]].astype(str).isin(buildings.keys())]

    # Delivery date fallback
    mask = (
        (df_bills[B["START"]] == "Not Available")
        & (df_bills[B["END"]] == "Not Available")
        & (df_bills[B["DELIVERY"]] != "Not Available")
    )
    if mask.any():
        df_bills.loc[mask, B["START"]] = df_bills.loc[mask, B["DELIVERY"]]
        df_bills.loc[mask, B["END"]] = pd.to_datetime(df_bills.loc[mask, B["DELIVERY"]]) + MonthEnd(1)
    if B["DELIVERY"] in df_bills.columns:
        df_bills = df_bills.drop(columns=[B["DELIVERY"]])

    # Parse bills
    bills_by_pm: Dict[str, List[UtilityBillData]] = {}
    for idx, row in df_bills.iterrows():
        try:
            pmid = str(row[B["PM_ID"]]).strip()
            start = pd.to_datetime(row[B["START"]]).date()
            end = pd.to_datetime(row[B["END"]]).date()
            if end <= start:
                raise ValueError("End date must be after start date")
            fuel_raw = str(row[B["METER_TYPE"]]).strip()
            unit_raw = str(row[B["USAGE_UNITS"]]).strip()
            fuel = FUEL_NAME_MAP.get(fuel_raw, fuel_raw)
            unit = UNIT_NAME_MAP.get(unit_raw, unit_raw)
            qty = float(row[B["USAGE_QTY"]])
            cost = None
            if B["COST"] in row and pd.notna(row[B["COST"]]):
                try:
                    cost = float(row[B["COST"]])
                except Exception:
                    cost = None
            ub = UtilityBillData(
                fuel_type=fuel,
                start_date=start,
                end_date=end,
                consumption=qty,
                units=unit,
                cost=cost,
            )
            bills_by_pm.setdefault(pmid, []).append(ub)
        except Exception as e:
            result.errors.append(ParseMessage(
                severity="error", sheet="Meter Entries", row=int(idx) if isinstance(idx, (int, float)) else None,
                message=f"Invalid bill row: {e}",
            ))

    result.buildings = list(buildings.values())
    result.bills_by_building = bills_by_pm
    return result

