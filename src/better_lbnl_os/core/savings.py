"""Savings estimation engine extracted from BETTER's Django application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

from better_lbnl_os.constants import MINIMUM_UTILITY_MONTHS
from better_lbnl_os.core.changepoint import piecewise_linear_5p
from better_lbnl_os.core.preprocessing import get_consecutive_bills
from better_lbnl_os.models import CalendarizedData
from better_lbnl_os.models.benchmarking import BenchmarkResult
from pydantic import BaseModel, Field


class SavingsEstimate(BaseModel):
    """Backwards-compatible savings estimate container."""

    energy_savings_kwh: float
    cost_savings_usd: float
    emissions_savings_kg_co2: float
    percent_reduction: float


class ComponentTotals(BaseModel):
    """Heating/baseload/cooling component totals."""

    heating_sensitive: float = 0.0
    baseload: float = 0.0
    cooling_sensitive: float = 0.0


class UsageTotals(BaseModel):
    """Aggregated usage totals for a given coefficient set."""

    energy_kwh: float = 0.0
    cost_usd: float = 0.0
    ghg_kg_co2: float = 0.0
    eui_kwh_per_m2: Optional[float] = None
    ghg_intensity_kg_co2_per_m2: Optional[float] = None
    energy_components: ComponentTotals = Field(default_factory=ComponentTotals)
    cost_components: ComponentTotals = Field(default_factory=ComponentTotals)
    ghg_components: ComponentTotals = Field(default_factory=ComponentTotals)


class ComponentSavings(BaseModel):
    """Component-level absolute savings for energy/cost/GHG."""

    energy_kwh: ComponentTotals = Field(default_factory=ComponentTotals)
    cost_usd: ComponentTotals = Field(default_factory=ComponentTotals)
    ghg_kg_co2: ComponentTotals = Field(default_factory=ComponentTotals)


class FuelSavingsResult(BaseModel):
    """Savings summary for a single energy type."""

    energy_type: str
    months: List[str]
    days_in_period: List[int]
    period_label: str
    current: UsageTotals
    target: UsageTotals
    typical: UsageTotals
    energy_savings_kwh: float
    energy_savings_percent: float
    cost_savings_usd: float
    cost_savings_percent: float
    ghg_savings_kg_co2: float
    ghg_savings_percent: float
    eui_savings_kwh_per_m2: Optional[float]
    ghg_intensity_reduction_kg_co2_per_m2: Optional[float]
    component_savings: ComponentSavings
    monthly_energy_kwh: List[float]
    monthly_cost_usd: List[float]
    monthly_ghg_kg_co2: List[float]
    valid: bool = True


class CombinedSavingsSummary(BaseModel):
    """Whole-building savings summary across fuels."""

    current: UsageTotals
    target: UsageTotals
    typical: UsageTotals
    energy_savings_kwh: float
    energy_savings_percent: float
    cost_savings_usd: float
    cost_savings_percent: float
    ghg_savings_kg_co2: float
    ghg_savings_percent: float
    eui_savings_kwh_per_m2: Optional[float]
    ghg_intensity_reduction_kg_co2_per_m2: Optional[float]
    component_savings: ComponentSavings
    valid: bool


class SavingsSummary(BaseModel):
    """Top-level savings report."""

    per_fuel: Dict[str, FuelSavingsResult]
    combined: CombinedSavingsSummary
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class _UsageArrays:
    months: List[str]
    days: np.ndarray
    total_energy: np.ndarray
    heating_energy: np.ndarray
    baseload_energy: np.ndarray
    cooling_energy: np.ndarray
    total_cost: np.ndarray
    heating_cost: np.ndarray
    baseload_cost: np.ndarray
    cooling_cost: np.ndarray
    total_ghg: np.ndarray
    heating_ghg: np.ndarray
    baseload_ghg: np.ndarray
    cooling_ghg: np.ndarray


def _ensure_calendarized_dict(calendarized: CalendarizedData | Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(calendarized, "to_legacy_dict"):
        return calendarized.to_legacy_dict()  # type: ignore[return-value]
    if isinstance(calendarized, dict):
        return calendarized
    raise TypeError("calendarized input must be CalendarizedData or dict")


def _ensure_benchmark_dict(benchmark: BenchmarkResult | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(benchmark, dict):
        return benchmark
    if isinstance(benchmark, BenchmarkResult):
        result: Dict[str, Any] = {}
        for energy_type in ("ELECTRICITY", "FOSSIL_FUEL"):
            et = getattr(benchmark, energy_type, None)
            if not et:
                continue
            coeffs: Dict[str, Dict[str, Optional[float]]] = {}
            for coeff in ("baseload", "heating_slope", "heating_change_point", "cooling_change_point", "cooling_slope"):
                coeff_result = getattr(et, coeff, None)
                if coeff_result is None:
                    continue
                coeffs[coeff] = {
                    "coefficient_value": getattr(coeff_result, "coefficient_value", None),
                    "target_value": getattr(coeff_result, "target_value", None),
                    "nominal_level": getattr(coeff_result, "nominal_level", None),
                }
            if coeffs:
                result[energy_type] = coeffs
        return result
    raise TypeError("benchmark_input must be BenchmarkResult or dict")


def _build_lookup(items: Iterable[str], values: Iterable[float]) -> Dict[str, float]:
    return {month: float(value) for month, value in zip(items, values)}


def _extract_series(legacy: Dict[str, Any], energy_type: str, months: List[str]) -> tuple[List[int], List[float], List[float]]:
    aggregated = legacy.get("aggregated", {})
    unit_prices_map = _build_lookup(
        aggregated.get("v_x", []),
        aggregated.get("dict_v_unit_prices", {}).get(energy_type, []),
    )
    ghg_map = _build_lookup(
        aggregated.get("v_x", []),
        aggregated.get("dict_v_ghg_factors", {}).get(energy_type, []),
    )
    days_map = _build_lookup(aggregated.get("v_x", []), aggregated.get("ls_n_days", []))
    days = [int(days_map.get(month, 30)) for month in months]
    unit_prices = [unit_prices_map.get(month, 0.0) for month in months]
    ghg_factors = [ghg_map.get(month, 0.0) for month in months]
    return days, unit_prices, ghg_factors


def _compute_usage_arrays(
    temperatures: List[float],
    coefficients: Dict[str, Optional[float]],
    floor_area: float,
    days: List[int],
    unit_prices: List[float],
    ghg_factors: List[float],
) -> _UsageArrays:
    arr_temp = np.asarray(temperatures, dtype=float)
    arr_days = np.asarray(days, dtype=float)
    arr_unit_prices = np.asarray(unit_prices, dtype=float)
    arr_ghg = np.asarray(ghg_factors, dtype=float)

    base = float(coefficients.get("baseload") or 0.0)
    total_eui = piecewise_linear_5p(
        arr_temp,
        coefficients.get("heating_slope"),
        coefficients.get("heating_change_point"),
        base,
        coefficients.get("cooling_change_point"),
        coefficients.get("cooling_slope"),
    )

    baseload_eui = np.full_like(total_eui, base)

    heating_eui = np.zeros_like(total_eui)
    if coefficients.get("heating_slope") is not None and coefficients.get("heating_change_point") is not None:
        mask = arr_temp <= float(coefficients["heating_change_point"])
        heating_eui[mask] = np.maximum(total_eui[mask] - baseload_eui[mask], 0)

    cooling_eui = np.zeros_like(total_eui)
    if coefficients.get("cooling_slope") is not None and coefficients.get("cooling_change_point") is not None:
        mask = arr_temp >= float(coefficients["cooling_change_point"])
        cooling_eui[mask] = np.maximum(total_eui[mask] - baseload_eui[mask], 0)

    total_energy = total_eui * arr_days * floor_area
    baseload_energy = baseload_eui * arr_days * floor_area
    heating_energy = heating_eui * arr_days * floor_area
    cooling_energy = cooling_eui * arr_days * floor_area

    price_mask = arr_unit_prices > 0
    total_cost = np.where(price_mask, total_energy * arr_unit_prices, 0.0)
    baseload_cost = np.where(price_mask, baseload_energy * arr_unit_prices, 0.0)
    heating_cost = np.where(price_mask, heating_energy * arr_unit_prices, 0.0)
    cooling_cost = np.where(price_mask, cooling_energy * arr_unit_prices, 0.0)

    ghg_mask = arr_ghg > 0
    total_ghg = np.where(ghg_mask, total_energy * arr_ghg, 0.0)
    baseload_ghg = np.where(ghg_mask, baseload_energy * arr_ghg, 0.0)
    heating_ghg = np.where(ghg_mask, heating_energy * arr_ghg, 0.0)
    cooling_ghg = np.where(ghg_mask, cooling_energy * arr_ghg, 0.0)

    return _UsageArrays(
        months=[],
        days=arr_days,
        total_energy=np.nan_to_num(total_energy, nan=0.0),
        heating_energy=np.nan_to_num(heating_energy, nan=0.0),
        baseload_energy=np.nan_to_num(baseload_energy, nan=0.0),
        cooling_energy=np.nan_to_num(cooling_energy, nan=0.0),
        total_cost=np.nan_to_num(total_cost, nan=0.0),
        heating_cost=np.nan_to_num(heating_cost, nan=0.0),
        baseload_cost=np.nan_to_num(baseload_cost, nan=0.0),
        cooling_cost=np.nan_to_num(cooling_cost, nan=0.0),
        total_ghg=np.nan_to_num(total_ghg, nan=0.0),
        heating_ghg=np.nan_to_num(heating_ghg, nan=0.0),
        baseload_ghg=np.nan_to_num(baseload_ghg, nan=0.0),
        cooling_ghg=np.nan_to_num(cooling_ghg, nan=0.0),
    )


def _assemble_usage_details(
    months: List[str],
    arrays: _UsageArrays,
) -> Dict[str, List[float]]:
    return {
        "ls_energy": arrays.total_energy.tolist(),
        "heating_sensitive_energy": arrays.heating_energy.tolist(),
        "baseload_energy": arrays.baseload_energy.tolist(),
        "cooling_sensitive_energy": arrays.cooling_energy.tolist(),
        "heating_sensitive_cost": arrays.heating_cost.tolist(),
        "baseload_cost": arrays.baseload_cost.tolist(),
        "cooling_sensitive_cost": arrays.cooling_cost.tolist(),
        "heating_sensitive_ghg": arrays.heating_ghg.tolist(),
        "baseload_ghg": arrays.baseload_ghg.tolist(),
        "cooling_sensitive_ghg": arrays.cooling_ghg.tolist(),
        "ls_months": months,
        "ls_n_days": arrays.days.astype(int).tolist(),
    }


def _summarize_usage(details: Dict[str, List[float]], floor_area: float) -> UsageTotals:
    energy_components = ComponentTotals(
        heating_sensitive=float(np.sum(details["heating_sensitive_energy"])),
        baseload=float(np.sum(details["baseload_energy"])),
        cooling_sensitive=float(np.sum(details["cooling_sensitive_energy"])),
    )
    cost_components = ComponentTotals(
        heating_sensitive=float(np.sum(details["heating_sensitive_cost"])),
        baseload=float(np.sum(details["baseload_cost"])),
        cooling_sensitive=float(np.sum(details["cooling_sensitive_cost"])),
    )
    ghg_components = ComponentTotals(
        heating_sensitive=float(np.sum(details["heating_sensitive_ghg"])),
        baseload=float(np.sum(details["baseload_ghg"])),
        cooling_sensitive=float(np.sum(details["cooling_sensitive_ghg"])),
    )

    energy_total = float(np.sum(details["ls_energy"]))
    cost_total = float(np.sum(details["baseload_cost"]))
    cost_total += float(np.sum(details["heating_sensitive_cost"]))
    cost_total += float(np.sum(details["cooling_sensitive_cost"]))
    ghg_total = float(np.sum(details["baseload_ghg"]))
    ghg_total += float(np.sum(details["heating_sensitive_ghg"]))
    ghg_total += float(np.sum(details["cooling_sensitive_ghg"]))

    eui = energy_total / floor_area if floor_area > 0 else None
    ghg_intensity = ghg_total / floor_area if floor_area > 0 else None

    return UsageTotals(
        energy_kwh=energy_total,
        cost_usd=cost_total,
        ghg_kg_co2=ghg_total,
        eui_kwh_per_m2=eui,
        ghg_intensity_kg_co2_per_m2=ghg_intensity,
        energy_components=energy_components,
        cost_components=cost_components,
        ghg_components=ghg_components,
    )


def _component_savings(current: UsageTotals, target: UsageTotals) -> ComponentSavings:
    def diff(comp_current: ComponentTotals, comp_target: ComponentTotals) -> ComponentTotals:
        return ComponentTotals(
            heating_sensitive=comp_current.heating_sensitive - comp_target.heating_sensitive,
            baseload=comp_current.baseload - comp_target.baseload,
            cooling_sensitive=comp_current.cooling_sensitive - comp_target.cooling_sensitive,
        )

    return ComponentSavings(
        energy_kwh=diff(current.energy_components, target.energy_components),
        cost_usd=diff(current.cost_components, target.cost_components),
        ghg_kg_co2=diff(current.ghg_components, target.ghg_components),
    )


def estimate_savings_for_fuel(
    benchmark_data: Dict[str, Any],
    calendarized: CalendarizedData | Dict[str, Any],
    *,
    floor_area: float,
    energy_type: str,
    window: int = MINIMUM_UTILITY_MONTHS,
) -> FuelSavingsResult:
    """Estimate savings for a single energy type."""

    if energy_type not in benchmark_data:
        raise ValueError(f"Benchmark data missing energy type: {energy_type}")

    legacy_calendarized = _ensure_calendarized_dict(calendarized)
    consecutive = get_consecutive_bills(calendarized, energy_type=energy_type, window=window)
    if not consecutive:
        raise ValueError("Not enough consecutive bills to estimate savings")

    months = consecutive["ls_months"]
    temperatures = consecutive["ls_degC"]
    days, unit_prices, ghg_factors = _extract_series(legacy_calendarized, energy_type, months)
    period_label = consecutive["period"]

    coeff_block = benchmark_data[energy_type]
    coeff_keys = ["baseload", "heating_slope", "heating_change_point", "cooling_change_point", "cooling_slope"]

    def select(step: str) -> Dict[str, Optional[float]]:
        return {key: coeff_block.get(key, {}).get(step) for key in coeff_keys}

    current_coeffs = select("coefficient_value")
    target_coeffs = select("target_value")
    typical_coeffs = select("nominal_level")

    current_arrays = _compute_usage_arrays(temperatures, current_coeffs, floor_area, days, unit_prices, ghg_factors)
    target_arrays = _compute_usage_arrays(temperatures, target_coeffs, floor_area, days, unit_prices, ghg_factors)
    typical_arrays = _compute_usage_arrays(temperatures, typical_coeffs, floor_area, days, unit_prices, ghg_factors)

    usage_current = _assemble_usage_details(months, current_arrays)
    usage_target = _assemble_usage_details(months, target_arrays)
    usage_typical = _assemble_usage_details(months, typical_arrays)

    current_totals = _summarize_usage(usage_current, floor_area)
    target_totals = _summarize_usage(usage_target, floor_area)
    typical_totals = _summarize_usage(usage_typical, floor_area)

    energy_savings = current_totals.energy_kwh - target_totals.energy_kwh
    cost_savings = current_totals.cost_usd - target_totals.cost_usd
    ghg_savings = current_totals.ghg_kg_co2 - target_totals.ghg_kg_co2

    energy_savings_pct = (energy_savings / current_totals.energy_kwh * 100) if current_totals.energy_kwh else 0.0
    cost_savings_pct = (cost_savings / current_totals.cost_usd * 100) if current_totals.cost_usd else 0.0
    ghg_savings_pct = (ghg_savings / current_totals.ghg_kg_co2 * 100) if current_totals.ghg_kg_co2 else 0.0

    eui_savings = None
    if current_totals.eui_kwh_per_m2 is not None and target_totals.eui_kwh_per_m2 is not None:
        eui_savings = current_totals.eui_kwh_per_m2 - target_totals.eui_kwh_per_m2

    ghg_intensity_reduction = None
    if (
        current_totals.ghg_intensity_kg_co2_per_m2 is not None
        and target_totals.ghg_intensity_kg_co2_per_m2 is not None
    ):
        ghg_intensity_reduction = (
            current_totals.ghg_intensity_kg_co2_per_m2 - target_totals.ghg_intensity_kg_co2_per_m2
        )

    component_savings = _component_savings(current_totals, target_totals)

    return FuelSavingsResult(
        energy_type=energy_type,
        months=months,
        days_in_period=days,
        period_label=period_label,
        current=current_totals,
        target=target_totals,
        typical=typical_totals,
        energy_savings_kwh=energy_savings,
        energy_savings_percent=energy_savings_pct,
        cost_savings_usd=cost_savings,
        cost_savings_percent=cost_savings_pct,
        ghg_savings_kg_co2=ghg_savings,
        ghg_savings_percent=ghg_savings_pct,
        eui_savings_kwh_per_m2=eui_savings,
        ghg_intensity_reduction_kg_co2_per_m2=ghg_intensity_reduction,
        component_savings=component_savings,
        monthly_energy_kwh=usage_current["ls_energy"],
        monthly_cost_usd=(current_arrays.total_cost).tolist(),
        monthly_ghg_kg_co2=(current_arrays.total_ghg).tolist(),
        valid=True,
    )


def _combine_usage_totals(results: Dict[str, FuelSavingsResult], floor_area: float) -> CombinedSavingsSummary:
    if not results:
        empty_totals = UsageTotals()
        empty_components = ComponentSavings()
        return CombinedSavingsSummary(
            current=empty_totals,
            target=empty_totals,
            typical=empty_totals,
            energy_savings_kwh=0.0,
            energy_savings_percent=0.0,
            cost_savings_usd=0.0,
            cost_savings_percent=0.0,
            ghg_savings_kg_co2=0.0,
            ghg_savings_percent=0.0,
            eui_savings_kwh_per_m2=None,
            ghg_intensity_reduction_kg_co2_per_m2=None,
            component_savings=empty_components,
            valid=False,
        )

    def add_usage(totals: Iterable[UsageTotals]) -> UsageTotals:
        energy = sum(t.energy_kwh for t in totals)
        cost = sum(t.cost_usd for t in totals)
        ghg = sum(t.ghg_kg_co2 for t in totals)
        components_energy = ComponentTotals(
            heating_sensitive=sum(t.energy_components.heating_sensitive for t in totals),
            baseload=sum(t.energy_components.baseload for t in totals),
            cooling_sensitive=sum(t.energy_components.cooling_sensitive for t in totals),
        )
        components_cost = ComponentTotals(
            heating_sensitive=sum(t.cost_components.heating_sensitive for t in totals),
            baseload=sum(t.cost_components.baseload for t in totals),
            cooling_sensitive=sum(t.cost_components.cooling_sensitive for t in totals),
        )
        components_ghg = ComponentTotals(
            heating_sensitive=sum(t.ghg_components.heating_sensitive for t in totals),
            baseload=sum(t.ghg_components.baseload for t in totals),
            cooling_sensitive=sum(t.ghg_components.cooling_sensitive for t in totals),
        )
        eui = energy / floor_area if floor_area > 0 else None
        ghg_intensity = ghg / floor_area if floor_area > 0 else None
        return UsageTotals(
            energy_kwh=energy,
            cost_usd=cost,
            ghg_kg_co2=ghg,
            eui_kwh_per_m2=eui,
            ghg_intensity_kg_co2_per_m2=ghg_intensity,
            energy_components=components_energy,
            cost_components=components_cost,
            ghg_components=components_ghg,
        )

    current_totals = add_usage(result.current for result in results.values())
    target_totals = add_usage(result.target for result in results.values())
    typical_totals = add_usage(result.typical for result in results.values())

    energy_savings = current_totals.energy_kwh - target_totals.energy_kwh
    cost_savings = current_totals.cost_usd - target_totals.cost_usd
    ghg_savings = current_totals.ghg_kg_co2 - target_totals.ghg_kg_co2

    energy_savings_pct = (energy_savings / current_totals.energy_kwh * 100) if current_totals.energy_kwh else 0.0
    cost_savings_pct = (cost_savings / current_totals.cost_usd * 100) if current_totals.cost_usd else 0.0
    ghg_savings_pct = (ghg_savings / current_totals.ghg_kg_co2 * 100) if current_totals.ghg_kg_co2 else 0.0

    eui_savings = None
    if current_totals.eui_kwh_per_m2 is not None and target_totals.eui_kwh_per_m2 is not None:
        eui_savings = current_totals.eui_kwh_per_m2 - target_totals.eui_kwh_per_m2

    ghg_intensity_reduction = None
    if (
        current_totals.ghg_intensity_kg_co2_per_m2 is not None
        and target_totals.ghg_intensity_kg_co2_per_m2 is not None
    ):
        ghg_intensity_reduction = (
            current_totals.ghg_intensity_kg_co2_per_m2 - target_totals.ghg_intensity_kg_co2_per_m2
        )

    component_savings = _component_savings(current_totals, target_totals)

    return CombinedSavingsSummary(
        current=current_totals,
        target=target_totals,
        typical=typical_totals,
        energy_savings_kwh=energy_savings,
        energy_savings_percent=energy_savings_pct,
        cost_savings_usd=cost_savings,
        cost_savings_percent=cost_savings_pct,
        ghg_savings_kg_co2=ghg_savings,
        ghg_savings_percent=ghg_savings_pct,
        eui_savings_kwh_per_m2=eui_savings,
        ghg_intensity_reduction_kg_co2_per_m2=ghg_intensity_reduction,
        component_savings=component_savings,
        valid=True,
    )


def estimate_savings(
    benchmark_input: BenchmarkResult | Dict[str, Any],
    calendarized: CalendarizedData | Dict[str, Any],
    *,
    floor_area: float,
    savings_target: Optional[str] = None,
) -> SavingsSummary:
    """Main entry point for savings estimation."""

    benchmark_dict = _ensure_benchmark_dict(benchmark_input)
    legacy_calendarized = _ensure_calendarized_dict(calendarized)

    per_fuel: Dict[str, FuelSavingsResult] = {}
    for energy_type in ("ELECTRICITY", "FOSSIL_FUEL"):
        if energy_type not in benchmark_dict:
            continue
        try:
            per_fuel[energy_type] = estimate_savings_for_fuel(
                benchmark_dict,
                legacy_calendarized,
                floor_area=floor_area,
                energy_type=energy_type,
                window=MINIMUM_UTILITY_MONTHS,
            )
        except ValueError:
            continue

    combined = _combine_usage_totals(per_fuel, floor_area)

    metadata = {
        "floor_area": floor_area,
        "savings_target": savings_target,
        "available_energy_types": list(per_fuel.keys()),
    }

    return SavingsSummary(
        per_fuel=per_fuel,
        combined=combined,
        metadata=metadata,
    )


__all__ = [
    "ComponentTotals",
    "UsageTotals",
    "ComponentSavings",
    "FuelSavingsResult",
    "CombinedSavingsSummary",
    "SavingsSummary",
    "estimate_savings_for_fuel",
    "estimate_savings",
    "SavingsEstimate",  # legacy re-export
]
