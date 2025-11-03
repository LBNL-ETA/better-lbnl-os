"""Preprocessing utilities for building analytics (slim, framework-free).

Calendarizes utility bills to monthly aggregates aligned with weather data.
"""

from __future__ import annotations

import calendar as _calendar
from dataclasses import dataclass, field
from datetime import timedelta

import pandas as pd

from better_lbnl_os.constants import CONVERSION_TO_KWH, MINIMUM_UTILITY_MONTHS
from better_lbnl_os.constants.energy import normalize_fuel_type, normalize_fuel_unit
from better_lbnl_os.models import UtilityBillData, WeatherData

# Import CalendarizedData and related from submodules to avoid circular imports
from better_lbnl_os.models.utility_bills import (
    CalendarizedData,
    EnergyAggregation,
    FuelAggregation,
)
from better_lbnl_os.models.weather import WeatherSeries


@dataclass
class CalendarizationOptions:
    """Options for calendarization processing."""

    energy_type_map: dict[str, str] | None = None
    conversion_to_kwh: dict[tuple[str, str], float] = field(
        default_factory=lambda: CONVERSION_TO_KWH
    )
    emission_factor_by_fuel: dict[str, float] | None = None  # kg CO2 per kWh
    fill_strategy: str = "mean"  # for unit_price/unit_emission; currently only 'mean' supported


def _infer_energy_type(fuel_type: str) -> str:
    f = (fuel_type or "").upper()
    if "ELECTRIC" in f:
        return "ELECTRICITY"
    if any(gas in f for gas in ["NATURAL", "GAS", "PROPANE", "FUEL", "OIL", "STEAM"]):
        return "FOSSIL_FUEL"
    # default to FOSSIL_FUEL for other fuels; callers can override via map
    return "FOSSIL_FUEL"


def calendarize_utility_bills(
    bills: list[UtilityBillData],
    floor_area: float,
    weather: list[WeatherData] | None = None,
    options: CalendarizationOptions | None = None,
) -> CalendarizedData:
    """Convert utility bills into calendar-month aggregates.

    Args:
        bills: List of UtilityBillData entries.
        floor_area: Building floor area (sq ft). If <= 0, EUI metrics are omitted.
        weather: Optional list of WeatherData to merge by (year, month).
        options: Optional CalendarizationOptions for mappings and factors.

    Returns:
        CalendarizedData model with typed weather, detailed, and aggregated data.

    Note:
        For Django/API compatibility, call `.to_legacy_dict()` on the result.
    """
    opts = options or CalendarizationOptions()

    if not bills:
        # Return empty CalendarizedData
        return CalendarizedData(
            weather=WeatherSeries(degC=[], degF=[]),
            detailed=FuelAggregation(),
            aggregated=EnergyAggregation(),
        )

    # ------------------ Prepare daily utility bill data ------------------
    rows = []
    for b in bills:
        rows.append(
            {
                "bill_start_date": b.start_date,
                "bill_end_date": b.end_date,
                "consumption": float(b.consumption),
                "Fuel_Type": b.fuel_type,
                "unit": b.units,
                "cost": float(b.cost) if b.cost is not None else None,
            }
        )
    df_bills = pd.DataFrame(rows)

    # Energy type mapping with heuristic fallback
    if opts.energy_type_map:
        df_bills["Energy_Type"] = (
            df_bills["Fuel_Type"]
            .map(opts.energy_type_map)
            .fillna(df_bills["Fuel_Type"].map(_infer_energy_type))
        )
    else:
        df_bills["Energy_Type"] = df_bills["Fuel_Type"].map(_infer_energy_type)
    df_bills["Fuel_Type"] = df_bills["Fuel_Type"].apply(normalize_fuel_type)
    df_bills["unit"] = df_bills["unit"].apply(normalize_fuel_unit)

    # Convert to kWh
    def _to_kwh(row) -> float:
        fuel_token = normalize_fuel_type(row.get("Fuel_Type"))
        unit_token = normalize_fuel_unit(row.get("unit"))
        factor = opts.conversion_to_kwh.get((fuel_token, unit_token))
        if factor is None:
            return row["consumption"]
        return row["consumption"] * factor

    df_bills["standard_consumption"] = df_bills.apply(_to_kwh, axis=1)

    # Emissions if factors provided
    if opts.emission_factor_by_fuel:
        df_bills["standard_emission"] = df_bills.apply(
            lambda x: x["standard_consumption"]
            * float(opts.emission_factor_by_fuel.get(x["Fuel_Type"], 0.0)),
            axis=1,
        )
    # Costs / unit price if cost provided
    if df_bills["cost"].notna().any():
        df_bills["standard_cost"] = df_bills["cost"].fillna(0.0)
        # derive unit price later as monthly_cost/monthly_kwh

    # Upsample to daily
    df_bills["bill_start_date"] = pd.to_datetime(df_bills["bill_start_date"])
    df_bills["bill_end_date"] = pd.to_datetime(df_bills["bill_end_date"])
    df_bills["days"] = (df_bills["bill_end_date"] - df_bills["bill_start_date"]).dt.days + 1

    daily_chunks: list[pd.DataFrame] = []
    for _, row in df_bills.iterrows():
        # guard invalid ranges
        if row["days"] <= 0:
            continue
        dates = [row["bill_start_date"] + timedelta(days=d) for d in range(int(row["days"]))]
        data = {
            "date": dates,
            "standard_consumption": row["standard_consumption"] / row["days"],
            "Fuel_Type": row["Fuel_Type"],
            "Energy_Type": row["Energy_Type"],
        }
        if "standard_emission" in df_bills.columns:
            data["standard_emission"] = row["standard_emission"] / row["days"]
        if "standard_cost" in df_bills.columns:
            data["standard_cost"] = row["standard_cost"] / row["days"]
        daily_chunks.append(pd.DataFrame(data))

    if not daily_chunks:
        # No valid days - return empty CalendarizedData
        return CalendarizedData(
            weather=WeatherSeries(degC=[], degF=[]),
            detailed=FuelAggregation(),
            aggregated=EnergyAggregation(),
        )

    df_daily = pd.concat(daily_chunks, ignore_index=True)
    df_daily["Year-Month"] = df_daily["date"].dt.strftime("%Y-%m")

    # ------------------ Monthly aggregates ------------------
    def _monthly_normalized(df: pd.DataFrame, floor: float, var: str) -> pd.DataFrame:
        # daily_standard_eui = kWh / floor_area / unique_days_in_month_group
        grp = df.groupby(["Year-Month", var])
        daily_eui = (
            (grp["standard_consumption"].sum() / float(floor) / grp["date"].nunique())
            if floor > 0
            else None
        )

        blocks = []
        if daily_eui is not None:
            blocks.append(
                pd.DataFrame(daily_eui).reset_index().rename(columns={0: "daily_standard_eui"})
            )
        if "standard_emission" in df.columns:
            unit_emission = grp["standard_emission"].sum() / grp["standard_consumption"].sum()
            blocks.append(
                pd.DataFrame(unit_emission).reset_index().rename(columns={0: "unit_emission"})
            )
        if "standard_cost" in df.columns:
            unit_price = grp["standard_cost"].sum() / grp["standard_consumption"].sum()
            blocks.append(pd.DataFrame(unit_price).reset_index().rename(columns={0: "unit_price"}))

        if not blocks:
            return pd.DataFrame(index=pd.Index([], name="Year-Month"))

        df_monthly = pd.concat(blocks)
        # Only pivot columns that actually exist
        pivot_values = []
        if "daily_standard_eui" in df_monthly.columns:
            pivot_values.append("daily_standard_eui")
        if "unit_emission" in df_monthly.columns:
            pivot_values.append("unit_emission")
        if "unit_price" in df_monthly.columns:
            pivot_values.append("unit_price")

        if not pivot_values:
            return pd.DataFrame(index=pd.Index([], name="Year-Month"))

        df_monthly = df_monthly.pivot_table(index="Year-Month", columns=var, values=pivot_values)
        df_monthly.columns = [
            f"{var} - {' - '.join(col[::-1]).strip()}" for col in df_monthly.columns.values
        ]
        return df_monthly

    df_norm_by_fuel = _monthly_normalized(df_daily, floor_area, var="Fuel_Type")
    df_norm_by_energy = _monthly_normalized(df_daily, floor_area, var="Energy_Type")
    df_norm = pd.concat([df_norm_by_fuel, df_norm_by_energy], axis=1)

    # Aggregated totals by energy/fuel type
    grouped_energy = df_daily.groupby(["Year-Month", "Energy_Type"])  # sums
    df_agg_energy = grouped_energy[["standard_consumption"]].sum().unstack().fillna(0)
    df_agg_energy.columns = [
        f"Energy_Type - {col[1]} - standard_consumption" for col in df_agg_energy.columns.values
    ]

    grouped_fuel = df_daily.groupby(["Year-Month", "Fuel_Type"])  # sums
    df_agg_fuel = grouped_fuel[["standard_consumption"]].sum().unstack().fillna(0)
    df_agg_fuel.columns = [
        f"Fuel_Type - {col[1]} - standard_consumption" for col in df_agg_fuel.columns.values
    ]

    # Add optional totals for emissions and costs
    if "standard_emission" in df_daily.columns:
        df_e_ghg = grouped_energy[["standard_emission"]].sum().unstack().fillna(0)
        df_e_ghg.columns = [
            f"Energy_Type - {c[1]} - standard_emission" for c in df_e_ghg.columns.values
        ]
        df_agg_energy = pd.concat([df_agg_energy, df_e_ghg], axis=1)

        df_f_ghg = grouped_fuel[["standard_emission"]].sum().unstack().fillna(0)
        df_f_ghg.columns = [
            f"Fuel_Type - {c[1]} - standard_emission" for c in df_f_ghg.columns.values
        ]
        df_agg_fuel = pd.concat([df_agg_fuel, df_f_ghg], axis=1)

    if "standard_cost" in df_daily.columns:
        df_e_cost = grouped_energy[["standard_cost"]].sum().unstack().fillna(0)
        df_e_cost.columns = [
            f"Energy_Type - {c[1]} - standard_cost" for c in df_e_cost.columns.values
        ]
        df_agg_energy = pd.concat([df_agg_energy, df_e_cost], axis=1)

        df_f_cost = grouped_fuel[["standard_cost"]].sum().unstack().fillna(0)
        df_f_cost.columns = [
            f"Fuel_Type - {c[1]} - standard_cost" for c in df_f_cost.columns.values
        ]
        df_agg_fuel = pd.concat([df_agg_fuel, df_f_cost], axis=1)

    # Merge normalized and aggregated frames
    df_monthly = pd.concat([df_agg_energy, df_agg_fuel, df_norm], axis=1)
    df_monthly = df_monthly.reset_index()

    # Add days in each month
    df_monthly["days_in_month"] = df_monthly["Year-Month"].apply(
        lambda ym: _calendar.monthrange(int(ym.split("-")[0]), int(ym.split("-")[1]))[1]
    )

    # Weather merge (optional)
    if weather:
        # Dedup by year, month — keep first occurrence
        seen = set()
        uniq: list[WeatherData] = []
        for w in weather:
            key = (w.year, w.month)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(w)

        df_w = pd.DataFrame(
            [{"year": w.year, "month": w.month, "avg_value_c": w.avg_temp_c} for w in uniq]
        )
        if not df_w.empty:
            df_w["avg_value_f"] = df_w["avg_value_c"].apply(lambda x: x * 1.8 + 32)
            df_w["Year-Month"] = pd.to_datetime(df_w[["year", "month"]].assign(day=1)).dt.strftime(
                "%Y-%m"
            )
            df_w = df_w.drop(columns=["year", "month"])
            df_monthly = df_monthly.merge(df_w, on="Year-Month", how="left")
        else:
            df_monthly["avg_value_c"] = 0.0
            df_monthly["avg_value_f"] = 0.0
    else:
        df_monthly["avg_value_c"] = 0.0
        df_monthly["avg_value_f"] = 0.0

    # To YYYY-MM-01 for x-axis consistency
    df_monthly["Year-Month"] = df_monthly["Year-Month"].astype(str) + "-01"

    # Fill strategy for unit metrics if present
    if opts.fill_strategy == "mean":
        for col in df_monthly.columns:
            if "unit_emission" in col or "unit_price" in col:
                if col in df_monthly:
                    df_monthly[col] = df_monthly[col].fillna(df_monthly[col].mean())
    df_monthly = df_monthly.fillna(0)

    cols = df_monthly.columns

    # Build output dicts
    # Period labels in ISO format YYYY-MM-01 for plotting/join keys
    periods = df_monthly["Year-Month"].astype(str).tolist()
    out_weather = {
        "degC": df_monthly["avg_value_c"].tolist(),
        "degF": df_monthly["avg_value_f"].tolist(),
    }

    def _subset(prefix: str, metric: str) -> dict[str, list[float]]:
        return {
            c.split(" - ")[1]: df_monthly[c].tolist()
            for c in cols
            if c.startswith(prefix) and c.endswith(metric)
        }

    {
        "periods": periods,
        "v_x": periods,  # alias for compatibility with Django naming
        "dict_v_energy": _subset("Fuel_Type", "standard_consumption"),
        "dict_v_costs": _subset("Fuel_Type", "standard_cost"),
        "dict_v_ghg": _subset("Fuel_Type", "standard_emission"),
        "dict_v_eui": _subset("Fuel_Type", "daily_standard_eui"),
        "dict_v_unit_prices": _subset("Fuel_Type", "unit_price"),
        "dict_v_ghg_factors": _subset("Fuel_Type", "unit_emission"),
    }

    # Convert periods to date objects
    period_dates = [pd.Timestamp(p).date() for p in periods]
    days_in_period = df_monthly["days_in_month"].tolist()

    # Build CalendarizedData model directly
    return CalendarizedData(
        weather=WeatherSeries(
            degC=out_weather["degC"],
            degF=out_weather["degF"],
        ),
        detailed=FuelAggregation(
            months=period_dates,
            days_in_period=days_in_period,
            energy_kwh=_subset("Fuel_Type", "standard_consumption"),
            cost=_subset("Fuel_Type", "standard_cost"),
            ghg_kg=_subset("Fuel_Type", "standard_emission"),
            daily_eui_kwh_per_m2=_subset("Fuel_Type", "daily_standard_eui"),
            unit_price_per_kwh=_subset("Fuel_Type", "unit_price"),
            unit_emission_kg_per_kwh=_subset("Fuel_Type", "unit_emission"),
        ),
        aggregated=EnergyAggregation(
            months=period_dates,
            days_in_period=days_in_period,
            energy_kwh=_subset("Energy_Type", "standard_consumption"),
            cost=_subset("Energy_Type", "standard_cost"),
            ghg_kg=_subset("Energy_Type", "standard_emission"),
            daily_eui_kwh_per_m2=_subset("Energy_Type", "daily_standard_eui"),
            unit_price_per_kwh=_subset("Energy_Type", "unit_price"),
            unit_emission_kg_per_kwh=_subset("Energy_Type", "unit_emission"),
        ),
    )


# Note: Single canonical API above returns CalendarizedData


# ------------------ Additional helpers for model preparation ------------------
def get_consecutive_months(
    calendarized: CalendarizedData | dict,
    energy_type: str = "ELECTRICITY",
    window: int = 12,
) -> dict[str, list]:
    """Select the last block of consecutive months with positive EUI.

    Args:
        calendarized: CalendarizedData model or legacy dict format
        energy_type: Energy type to extract (ELECTRICITY or FOSSIL_FUEL)
        window: Minimum consecutive months required

    Returns:
        Dict with keys: months, degC, eui, days, period
        Empty dict if insufficient data

    Note:
        Prefers CalendarizedData for type-safe property access.
        Falls back to dict for backward compatibility.
    """
    # Fast path: Work with CalendarizedData directly (type-safe)
    if isinstance(calendarized, CalendarizedData):
        try:
            periods = [m.strftime("%Y-%m-01") for m in calendarized.aggregated.months]
            days = list(calendarized.aggregated.days_in_period)
            eui_map = calendarized.aggregated.daily_eui_kwh_per_m2
            degC = list(calendarized.weather.degC)
        except Exception:
            return {}

        if not periods or energy_type not in eui_map:
            return {}
    else:
        # Fallback: Support legacy dict (for Django compatibility)
        try:
            aggregated = calendarized.get("aggregated", {})
            # Support both modern and legacy key names
            periods = aggregated.get("periods", aggregated.get("v_x"))
            days = aggregated.get("days_in_period", aggregated.get("ls_n_days"))
            eui_map = aggregated.get("dict_v_eui", {})
            degC = calendarized.get("weather", {}).get("degC", [])
        except Exception:
            return {}

        if not periods or energy_type not in eui_map:
            return {}

    df = pd.DataFrame(
        {
            "month": pd.to_datetime(pd.Series(periods)),
            "eui": pd.Series(eui_map[energy_type]).astype(float),
            "degC": pd.Series(degC).astype(float),
            "days": pd.Series(days).astype(int),
        }
    )

    # Keep positive EUI months and sort
    df = df[df["eui"] > 0].sort_values("month").reset_index(drop=True)
    if df.empty:
        return {}

    # Determine consecutive month blocks using Period arithmetic
    p = df["month"].dt.to_period("M")
    # For periods, diff() returns number of periods as difference
    # Convert to integer representation to check consecutiveness
    period_ints = p.astype("int64")
    int_diff = period_ints.diff()
    # Consecutive months have a difference of 1
    is_consec = (int_diff == 1) | int_diff.isna()
    block = (~is_consec).cumsum()
    df["block"] = block

    # Filter valid blocks >= window
    sizes = df.groupby("block").size()
    valid_blocks = sizes[sizes >= window].index.tolist()
    if not valid_blocks:
        return {}

    # Take the last valid block chronologically, then last `window` rows
    last_block = valid_blocks[-1]
    sub = df[df["block"] == last_block].tail(window)
    start = sub["month"].iloc[0].strftime("%Y-%m")
    end = sub["month"].iloc[-1].strftime("%Y-%m")

    return {
        "months": sub["month"].dt.strftime("%Y-%m-01").tolist(),
        "degC": sub["degC"].tolist(),
        "eui": sub["eui"].tolist(),
        "days": sub["days"].tolist(),
        "period": f"{start} to {end}",
    }


def trim_series(eui: list[float], degc: list[float]) -> tuple[list[float], list[float]]:
    """Trim leading and trailing zeros from EUI while keeping arrays aligned.

    If arrays are empty or lengths mismatch, returns inputs unchanged.
    """
    try:
        if len(eui) != len(degc) or len(eui) == 0:
            return eui, degc
        i0 = 0
        i1 = len(eui)
        while i0 < i1 and float(eui[i0]) == 0:
            i0 += 1
        while i1 > i0 and float(eui[i1 - 1]) == 0:
            i1 -= 1
        return eui[i0:i1], degc[i0:i1]
    except Exception:
        return eui, degc


def get_consecutive_bills(
    calendarized: dict | CalendarizedData,
    energy_type: str = "ELECTRICITY",
    window: int = MINIMUM_UTILITY_MONTHS,
) -> dict[str, list]:
    """Return the latest block of consecutive months with positive EUI.

    .. deprecated::
        Use :func:`get_consecutive_months` instead. This function is maintained
        only for backward compatibility with Django integration and returns keys
        with legacy `ls_` prefixes.

    Returns:
        Dict with keys: ls_months, ls_n_days, ls_eui, ls_degC, period
    """
    import warnings

    warnings.warn(
        "get_consecutive_bills() is deprecated. Use get_consecutive_months() instead, "
        "which returns modern key names (months, days, eui, degC).",
        DeprecationWarning,
        stacklevel=2,
    )

    if hasattr(calendarized, "to_legacy_dict"):
        calendarized = calendarized.to_legacy_dict()  # type: ignore[assignment]

    try:
        aggregated = calendarized["aggregated"]
        weather = calendarized["weather"]
        months = aggregated["v_x"]
        days = aggregated["ls_n_days"]
        eui_map = aggregated["dict_v_eui"].get(energy_type)
        temperatures = weather.get("degC", [])
    except Exception:
        return {}

    if not eui_map:
        return {}

    length = min(len(months), len(days), len(eui_map), len(temperatures))
    if length == 0:
        return {}

    months = months[-length:]
    days = days[-length:]
    eui_values = eui_map[-length:]
    temperatures = temperatures[-length:]

    df = pd.DataFrame(
        {
            "month": pd.to_datetime(months, errors="coerce"),
            "ls_n_days": pd.to_numeric(days, errors="coerce"),
            "eui": pd.to_numeric(eui_values, errors="coerce"),
            "degC": pd.to_numeric(temperatures, errors="coerce"),
        }
    ).dropna(subset=["month", "ls_n_days", "eui", "degC"])

    if df.empty:
        return {}

    df = df.sort_values("month")
    df = df[df["eui"] > 0]
    if df.empty:
        return {}

    df["month_diff"] = df["month"].diff().dt.days.abs()
    is_consecutive = df["month_diff"].between(27, 31, inclusive="both").fillna(False)
    df["block"] = (~is_consecutive).cumsum()

    blocks = df.groupby("block").filter(lambda g: len(g) >= window)
    if blocks.empty:
        return {}

    last_block_id = blocks["block"].iloc[-1]
    window_block = blocks[blocks["block"] == last_block_id].tail(window)

    start_month = window_block["month"].iloc[0].strftime("%Y-%m")
    end_month = window_block["month"].iloc[-1].strftime("%Y-%m")

    return {
        "ls_months": window_block["month"].dt.strftime("%Y-%m-%d").tolist(),
        "ls_n_days": window_block["ls_n_days"].astype(int).tolist(),
        "ls_eui": window_block["eui"].tolist(),
        "ls_degC": window_block["degC"].tolist(),
        "period": f"{start_month} to {end_month}",
    }
