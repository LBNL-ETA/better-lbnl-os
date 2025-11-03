"""Energy efficiency recommendation engine.

This module extracts the BETTER recommendation logic so the core symptom
checks and measure mappings can be reused outside the Django application.
Only the 15 top-level measures live here; detailed metadata such as
secondary measures or resource links remain the responsibility of the host
application.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from better_lbnl_os.constants import (
    SYMPTOM_COEFFICIENTS,
    SYMPTOM_DESCRIPTIONS,
    TOP_LEVEL_EE_MEASURES,
    BuildingSpaceType,
)
from better_lbnl_os.models.benchmarking import BenchmarkResult
from better_lbnl_os.models.recommendations import (
    EEMeasureRecommendation,
    EERecommendationResult,
    InefficiencySymptom,
)

BETTER_MEASURES = TOP_LEVEL_EE_MEASURES


def _benchmark_result_to_dict(
    benchmark_input: BenchmarkResult | dict[str, Any],
) -> dict[str, dict[str, dict[str, float | None]]]:
    """Normalise results to the legacy benchmarking dictionary structure."""
    if isinstance(benchmark_input, dict):
        return benchmark_input

    if not isinstance(benchmark_input, BenchmarkResult):
        raise TypeError("benchmark_input must be BenchmarkResult or benchmarking dict")

    result: dict[str, dict[str, dict[str, float | None]]] = {}
    for energy_type in ("ELECTRICITY", "FOSSIL_FUEL"):
        et_result = getattr(benchmark_input, energy_type, None)
        if not et_result:
            continue
        coeffs: dict[str, dict[str, float | None]] = {}
        for coeff in SYMPTOM_COEFFICIENTS:
            coeff_result = getattr(et_result, coeff, None)
            if not coeff_result:
                continue
            coeffs[coeff] = {
                "coefficient_value": getattr(coeff_result, "coefficient_value", None),
                "target_value": getattr(coeff_result, "target_value", None),
            }
        if coeffs:
            result[energy_type] = coeffs
    return result


def _lt(value: float | None, target: float | None) -> bool:
    return value is not None and target is not None and value < target


def _gt(value: float | None, target: float | None) -> bool:
    return value is not None and target is not None and value > target


def _severity_lt(value: float | None, target: float | None) -> float | None:
    if value is None or target is None:
        return None
    return max(0.0, target - value)


def _severity_gt(value: float | None, target: float | None) -> float | None:
    if value is None or target is None:
        return None
    return max(0.0, value - target)


def _first_trigger_lt(
    pairs: Iterable[tuple[float | None, float | None]],
) -> tuple[float | None, float | None, float | None] | None:
    for value, target in pairs:
        if _lt(value, target):
            return value, target, _severity_lt(value, target)
    return None


def _first_trigger_gt(
    pairs: Iterable[tuple[float | None, float | None]],
) -> tuple[float | None, float | None, float | None] | None:
    for value, target in pairs:
        if _gt(value, target):
            return value, target, _severity_gt(value, target)
    return None


def detect_symptoms(benchmark_input: BenchmarkResult | dict[str, Any]) -> list[InefficiencySymptom]:
    """Detect inefficiency symptoms using the legacy BETTER rules."""
    data = _benchmark_result_to_dict(benchmark_input)

    def _val(energy: str, coeff: str, key: str) -> float | None:
        return data.get(energy, {}).get(coeff, {}).get(key)

    symptoms: list[InefficiencySymptom] = []

    trigger = _first_trigger_lt(
        [
            (
                _val("ELECTRICITY", "cooling_change_point", "coefficient_value"),
                _val("ELECTRICITY", "cooling_change_point", "target_value"),
            ),
            (
                _val("FOSSIL_FUEL", "cooling_change_point", "coefficient_value"),
                _val("FOSSIL_FUEL", "cooling_change_point", "target_value"),
            ),
        ]
    )
    if trigger:
        value, target, severity = trigger
        symptoms.append(
            InefficiencySymptom(
                symptom_id="low_cooling_change_point",
                description=SYMPTOM_DESCRIPTIONS["low_cooling_change_point"],
                severity=severity,
                detected_value=value,
                threshold_value=target,
                metric="cooling_change_point",
            )
        )

    trigger = _first_trigger_gt(
        [
            (
                _val("ELECTRICITY", "heating_change_point", "coefficient_value"),
                _val("ELECTRICITY", "heating_change_point", "target_value"),
            ),
            (
                _val("FOSSIL_FUEL", "heating_change_point", "coefficient_value"),
                _val("FOSSIL_FUEL", "heating_change_point", "target_value"),
            ),
        ]
    )
    if trigger:
        value, target, severity = trigger
        symptoms.append(
            InefficiencySymptom(
                symptom_id="high_heating_change_point",
                description=SYMPTOM_DESCRIPTIONS["high_heating_change_point"],
                severity=severity,
                detected_value=value,
                threshold_value=target,
                metric="heating_change_point",
            )
        )

    value = _val("ELECTRICITY", "baseload", "coefficient_value")
    target = _val("ELECTRICITY", "baseload", "target_value")
    if _gt(value, target):
        symptoms.append(
            InefficiencySymptom(
                symptom_id="high_electricity_baseload",
                description=SYMPTOM_DESCRIPTIONS["high_electricity_baseload"],
                severity=_severity_gt(value, target),
                detected_value=value,
                threshold_value=target,
                metric="baseload",
            )
        )

    trigger = _first_trigger_gt(
        [
            (
                _val("ELECTRICITY", "cooling_slope", "coefficient_value"),
                _val("ELECTRICITY", "cooling_slope", "target_value"),
            ),
            (
                _val("FOSSIL_FUEL", "cooling_slope", "coefficient_value"),
                _val("FOSSIL_FUEL", "cooling_slope", "target_value"),
            ),
        ]
    )
    if trigger:
        value, target, severity = trigger
        symptoms.append(
            InefficiencySymptom(
                symptom_id="high_cooling_sensitivity",
                description=SYMPTOM_DESCRIPTIONS["high_cooling_sensitivity"],
                severity=severity,
                detected_value=value,
                threshold_value=target,
                metric="cooling_slope",
            )
        )

    trigger = _first_trigger_lt(
        [
            (
                _val("ELECTRICITY", "heating_slope", "coefficient_value"),
                _val("ELECTRICITY", "heating_slope", "target_value"),
            ),
            (
                _val("FOSSIL_FUEL", "heating_slope", "coefficient_value"),
                _val("FOSSIL_FUEL", "heating_slope", "target_value"),
            ),
        ]
    )
    if trigger:
        value, target, severity = trigger
        symptoms.append(
            InefficiencySymptom(
                symptom_id="high_heating_sensitivity",
                description=SYMPTOM_DESCRIPTIONS["high_heating_sensitivity"],
                severity=severity,
                detected_value=value,
                threshold_value=target,
                metric="heating_slope",
            )
        )

    value = _val("ELECTRICITY", "heating_change_point", "coefficient_value")
    target = _val("ELECTRICITY", "heating_change_point", "target_value")
    if _gt(value, target):
        symptoms.append(
            InefficiencySymptom(
                symptom_id="high_electricity_heating_change_point",
                description=SYMPTOM_DESCRIPTIONS["high_electricity_heating_change_point"],
                severity=_severity_gt(value, target),
                detected_value=value,
                threshold_value=target,
                metric="heating_change_point",
            )
        )

    value = _val("ELECTRICITY", "cooling_slope", "coefficient_value")
    target = _val("ELECTRICITY", "cooling_slope", "target_value")
    if _gt(value, target):
        symptoms.append(
            InefficiencySymptom(
                symptom_id="high_electricity_cooling_sensitivity",
                description=SYMPTOM_DESCRIPTIONS["high_electricity_cooling_sensitivity"],
                severity=_severity_gt(value, target),
                detected_value=value,
                threshold_value=target,
                metric="cooling_slope",
            )
        )

    value = _val("ELECTRICITY", "heating_slope", "coefficient_value")
    target = _val("ELECTRICITY", "heating_slope", "target_value")
    if _lt(value, target):
        symptoms.append(
            InefficiencySymptom(
                symptom_id="high_electricity_heating_sensitivity",
                description=SYMPTOM_DESCRIPTIONS["high_electricity_heating_sensitivity"],
                severity=_severity_lt(value, target),
                detected_value=value,
                threshold_value=target,
                metric="heating_slope",
            )
        )

    value = _val("FOSSIL_FUEL", "baseload", "coefficient_value")
    target = _val("FOSSIL_FUEL", "baseload", "target_value")
    if _gt(value, target):
        symptoms.append(
            InefficiencySymptom(
                symptom_id="high_fossil_fuel_baseload",
                description=SYMPTOM_DESCRIPTIONS["high_fossil_fuel_baseload"],
                severity=_severity_gt(value, target),
                detected_value=value,
                threshold_value=target,
                metric="baseload",
            )
        )

    return symptoms


def map_symptoms_to_measures(symptoms: list[InefficiencySymptom]) -> list[EEMeasureRecommendation]:
    """Map detected symptoms to the top-level BETTER measures."""
    symptom_ids = {symptom.symptom_id for symptom in symptoms}
    recommendations: dict[str, EEMeasureRecommendation] = {}

    def _add_measure(
        measure_token: str,
        triggers: str | Iterable[str],
        *,
        priority: str = "medium",
    ) -> None:
        name = BETTER_MEASURES.get(measure_token)
        if not name:
            return
        if isinstance(triggers, str):
            trigger_list = [triggers]
        else:
            trigger_list = [t for t in triggers if t]
        if not trigger_list:
            return
        if measure_token in recommendations:
            existing = recommendations[measure_token]
            for trig in trigger_list:
                if trig not in existing.triggered_by:
                    existing.triggered_by.append(trig)
        else:
            recommendations[measure_token] = EEMeasureRecommendation(
                measure_id=measure_token,
                name=name,
                triggered_by=trigger_list,
                priority=priority,
            )

    if "low_cooling_change_point" in symptom_ids:
        _add_measure("INCREASE_COOLING_SETPOINTS", "low_cooling_change_point")
        _add_measure("ADD_FIX_ECONOMIZERS", "low_cooling_change_point")

    if "high_heating_change_point" in symptom_ids:
        _add_measure("DECREASE_HEATING_SETPOINTS", "high_heating_change_point")

    if (
        "high_electricity_baseload" in symptom_ids
        or {
            "low_cooling_change_point",
            "high_heating_change_point",
        }
        & symptom_ids
    ):
        triggers = [
            sid
            for sid in (
                "high_electricity_baseload",
                "low_cooling_change_point",
                "high_heating_change_point",
            )
            if sid in symptom_ids
        ]
        _add_measure("REDUCE_EQUIPMENT_SCHEDULES", triggers)

    if "high_cooling_sensitivity" in symptom_ids:
        _add_measure("INCREASE_COOLING_SYSTEM_EFFICIENCY", "high_cooling_sensitivity")

    if "high_heating_sensitivity" in symptom_ids:
        _add_measure("INCREASE_HEATING_SYSTEM_EFFICIENCY", "high_heating_sensitivity")

    if "high_electricity_baseload" in symptom_ids:
        _add_measure("REDUCE_LIGHTING_LOAD", "high_electricity_baseload")
        _add_measure("REDUCE_PLUG_LOADS", "high_electricity_baseload")

    if "high_electricity_heating_sensitivity" in symptom_ids:
        _add_measure(
            "USE_HIGH_EFFICIENCY_HEAT_PUMP_FOR_HEATING",
            "high_electricity_heating_sensitivity",
        )

    if "high_fossil_fuel_baseload" in symptom_ids:
        _add_measure(
            "UPGRADE_TO_SUSTAINABLE_RESOURCES_FOR_WATER_HEATING",
            "high_fossil_fuel_baseload",
        )

    ventilation_group = {
        "high_heating_change_point",
        "high_cooling_sensitivity",
        "high_heating_sensitivity",
    }
    if len(ventilation_group & symptom_ids) >= 2:
        _add_measure(
            "ENSURE_ADEQUATE_VENTILATION_RATE",
            ventilation_group & symptom_ids,
        )

    envelope_group = {
        "high_electricity_heating_change_point",
        "high_electricity_cooling_sensitivity",
        "high_electricity_heating_sensitivity",
    }
    if len(envelope_group & symptom_ids) >= 2:
        triggers_set = envelope_group & symptom_ids
        _add_measure("DECREASE_INFILTRATION", triggers_set)
        _add_measure("ADD_WALL_CEILING_ROOF_INSULATION", triggers_set)
        _add_measure("UPGRADE_WINDOWS_TO_IMPROVE_THERMAL_EFFICIENCY", triggers_set)

    if {
        "high_cooling_sensitivity",
        "low_cooling_change_point",
    } & symptom_ids:
        triggers = [
            sid
            for sid in ("high_cooling_sensitivity", "low_cooling_change_point")
            if sid in symptom_ids
        ]
        _add_measure("UPGRADE_WINDOWS_TO_REDUCE_SOLAR_HEAT_GAIN", triggers)

    return list(recommendations.values())


def recommend_ee_measures(
    benchmark_input: BenchmarkResult | dict[str, Any],
    *,
    building_type: BuildingSpaceType | None = None,
) -> EERecommendationResult:
    """Produce EE recommendations for the provided benchmarking results."""
    symptoms = detect_symptoms(benchmark_input)
    recommendations = map_symptoms_to_measures(symptoms)
    recommendations.sort(key=lambda rec: rec.measure_id)

    metadata = {
        "total_symptoms": len(symptoms),
        "total_recommendations": len(recommendations),
        "building_type": building_type.name if building_type else None,
        "symptom_ids": [symptom.symptom_id for symptom in symptoms],
    }

    return EERecommendationResult(
        symptoms=symptoms,
        recommendations=recommendations,
        metadata=metadata,
    )


__all__ = [
    "BETTER_MEASURES",
    "detect_symptoms",
    "map_symptoms_to_measures",
    "recommend_ee_measures",
]
