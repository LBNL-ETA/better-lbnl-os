"""Reader for Energy Star Portfolio Manager custom download format."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from pandas.tseries.offsets import MonthEnd

from better_lbnl_os.constants import SQFT_TO_SQM, normalize_space_type
from better_lbnl_os.constants.energy import normalize_fuel_type, normalize_fuel_unit
from better_lbnl_os.constants.template_parsing import PM_BILLS_HEADERS as B
from better_lbnl_os.constants.template_parsing import PM_META_HEADERS as M
from better_lbnl_os.models import BuildingData, UtilityBillData

from .types import ParsedPortfolio, ParseMessage

PM_SKIPROWS_DEFAULT = 5


def _read_pm_sheet(
    file_like,
    sheet_name: str,
    required_columns: Sequence[str],
    *,
    parse_dates: Sequence[int] | None = None,
) -> tuple[pd.DataFrame | None, Exception | None]:
    """Read a Portfolio Manager sheet, trying with and without skiprows."""
    base_kwargs: dict[str, object] = {}
    if parse_dates is not None:
        base_kwargs["parse_dates"] = list(parse_dates)

    attempts = [
        {**base_kwargs, "skiprows": PM_SKIPROWS_DEFAULT},
        base_kwargs,
    ]
    last_error: Exception | None = None

    for kwargs in attempts:
        try:
            if hasattr(file_like, "seek"):
                file_like.seek(0)
            df = pd.read_excel(file_like, sheet_name=sheet_name, **kwargs)
        except Exception as exc:
            last_error = exc
            continue

        df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            last_error = ValueError(f"Missing columns: {missing}")
            continue

        return df, None

    return None, last_error


def read_portfolio_manager(file_like) -> ParsedPortfolio:
    """Parse a Portfolio Manager custom download workbook into a ParsedPortfolio."""
    result = ParsedPortfolio(metadata={"template_type": "portfolio_manager", "unit_system": "IP"})

    # Properties sheet (try skipping instructional rows first, then fallback)
    df_meta, meta_error = _read_pm_sheet(file_like, "Properties", list(M.values()))
    if df_meta is None:
        result.errors.append(
            ParseMessage(
                severity="error",
                sheet="Properties",
                message="Failed to read sheet with expected headers"
                + (f": {meta_error}" if meta_error else ""),
            )
        )
        return result

    # Filter rows with PM ID
    df_meta = df_meta[df_meta[M["PM_ID"]].notna()].copy()

    # Build BuildingData; convert floor area to SI if units are Sq. Ft.
    buildings: dict[str, BuildingData] = {}
    for _, row in df_meta.iterrows():
        try:
            pmid = str(row[M["PM_ID"]]).strip()
            name = str(row[M["PROP_NAME"]]).strip()
            city = str(row[M["CITY"]]).strip()
            state = str(row[M["STATE"]]).strip()
            postal = str(row[M["POSTAL"]]).strip()
            loc = f"{city}, {state} {postal}".strip()
            gfa_units = str(row[M["GFA_UNITS"]]).strip()
            gfa = float(row[M["GFA"]])
            if gfa_units.lower().startswith("sq"):
                gfa *= SQFT_TO_SQM
            space_type_raw = str(row[M["SPACE_TYPE"]]).strip()
            space_type = normalize_space_type(space_type_raw)
            b = BuildingData(name=name, floor_area=gfa, space_type=space_type, location=loc)
            buildings[pmid] = b
        except Exception as e:
            result.errors.append(
                ParseMessage(
                    severity="error", sheet="Properties", message=f"Invalid building row: {e}"
                )
            )

    # Meter Entries sheet (same skiprows handling)
    df_bills, bills_error = _read_pm_sheet(file_like, "Meter Entries", list(B.values()))
    if df_bills is None:
        result.errors.append(
            ParseMessage(
                severity="error",
                sheet="Meter Entries",
                message="Failed to read sheet with expected headers"
                + (f": {bills_error}" if bills_error else ""),
            )
        )
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
        df_bills.loc[mask, B["END"]] = pd.to_datetime(df_bills.loc[mask, B["DELIVERY"]]) + MonthEnd(
            1
        )
    if B["DELIVERY"] in df_bills.columns:
        df_bills = df_bills.drop(columns=[B["DELIVERY"]])

    # Parse bills
    bills_by_pm: dict[str, list[UtilityBillData]] = {}
    for idx, row in df_bills.iterrows():
        try:
            pmid = str(row[B["PM_ID"]]).strip()
            start = pd.to_datetime(row[B["START"]]).date()
            end = pd.to_datetime(row[B["END"]]).date()
            if end <= start:
                raise ValueError("End date must be after start date")
            fuel_raw = str(row[B["METER_TYPE"]]).strip()
            unit_raw = str(row[B["USAGE_UNITS"]]).strip()
            qty = float(row[B["USAGE_QTY"]])
            fuel = normalize_fuel_type(fuel_raw)
            unit = normalize_fuel_unit(unit_raw)
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
            result.errors.append(
                ParseMessage(
                    severity="error",
                    sheet="Meter Entries",
                    row=int(idx) if isinstance(idx, (int, float)) else None,
                    message=f"Invalid bill row: {e}",
                )
            )

    result.buildings = list(buildings.values())
    result.bills_by_building = bills_by_pm
    return result
