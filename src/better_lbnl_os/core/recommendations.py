"""Energy efficiency recommendation engine.

This module extracts the BETTER recommendation logic so the core symptom
checks and measure mappings can be reused outside the Django application.
Only the 15 top-level measures live here; detailed metadata such as
secondary measures or resource links remain the responsibility of the host
application.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Union

from better_lbnl_os.constants import BuildingSpaceType, TOP_LEVEL_EE_MEASURES
from better_lbnl_os.models.benchmarking import BenchmarkResult
from better_lbnl_os.models.recommendations import (
    EERecommendationResult,
    EEMeasureRecommendation,
    InefficiencySymptom,
)

BETTER_MEASURES = TOP_LEVEL_EE_MEASURES

SYMBOLIC_DESCRIPTIONS = {
    "low_cooling_change_point": "Cooling turns on earlier than the target change-point.",
    "high_heating_change_point": "Heating change-point is higher than the target value.",
    "high_electricity_baseload": "Electricity baseload exceeds the target level.",
    "high_cooling_sensitivity": "Cooling usage increases faster than targeted with temperature.",
    "high_heating_sensitivity": "Heating usage increases faster than targeted in cold weather.",
    "high_electricity_heating_change_point": "Electric heating change-point is above target.",
    "high_electricity_cooling_sensitivity": "Electric cooling slope is above target.",
    "high_electricity_heating_sensitivity": "Electric heating slope is more negative than target.",
    "high_fossil_fuel_baseload": "Fossil fuel baseload exceeds target.",
}

COEFFICIENTS: Iterable[str] = (
    "heating_slope",
    "heating_change_point",
    "baseload",
    "cooling_change_point",
    "cooling_slope",
)


def _benchmark_result_to_dict(
    benchmark_input: Union[BenchmarkResult, Dict[str, Any]]
) -> Dict[str, Dict[str, Dict[str, Optional[float]]]]:
    """Normalise results to the legacy benchmarking dictionary structure."""

    if isinstance(benchmark_input, dict):
        return benchmark_input

    if not isinstance(benchmark_input, BenchmarkResult):
        raise TypeError("benchmark_input must be BenchmarkResult or benchmarking dict")

    result: Dict[str, Dict[str, Dict[str, Optional[float]]]] = {}
    for energy_type in ("ELECTRICITY", "FOSSIL_FUEL"):
        et_result = getattr(benchmark_input, energy_type, None)
        if not et_result:
            continue
        coeffs: Dict[str, Dict[str, Optional[float]]] = {}
        for coeff in COEFFICIENTS:
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


def _lt(value: Optional[float], target: Optional[float]) -> bool:
    return value is not None and target is not None and value < target


def _gt(value: Optional[float], target: Optional[float]) -> bool:
    return value is not None and target is not None and value > target


def _severity_lt(value: Optional[float], target: Optional[float]) -> Optional[float]:
    if value is None or target is None:
        return None
    return max(0.0, target - value)


def _severity_gt(value: Optional[float], target: Optional[float]) -> Optional[float]:
    if value is None or target is None:
        return None
    return max(0.0, value - target)


def _first_trigger_lt(
    pairs: Iterable[tuple[Optional[float], Optional[float]]]
) -> Optional[tuple[Optional[float], Optional[float], Optional[float]]]:
    for value, target in pairs:
        if _lt(value, target):
            return value, target, _severity_lt(value, target)
    return None


def _first_trigger_gt(
    pairs: Iterable[tuple[Optional[float], Optional[float]]]
) -> Optional[tuple[Optional[float], Optional[float], Optional[float]]]:
    for value, target in pairs:
        if _gt(value, target):
            return value, target, _severity_gt(value, target)
    return None


def detect_symptoms(
    benchmark_input: Union[BenchmarkResult, Dict[str, Any]]
) -> List[InefficiencySymptom]:
    """Detect inefficiency symptoms using the legacy BETTER rules."""

    data = _benchmark_result_to_dict(benchmark_input)

    def _val(energy: str, coeff: str, key: str) -> Optional[float]:
        return data.get(energy, {}).get(coeff, {}).get(key)

    symptoms: List[InefficiencySymptom] = []

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
                description=SYMBOLIC_DESCRIPTIONS["low_cooling_change_point"],
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
                description=SYMBOLIC_DESCRIPTIONS["high_heating_change_point"],
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
                description=SYMBOLIC_DESCRIPTIONS["high_electricity_baseload"],
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
                description=SYMBOLIC_DESCRIPTIONS["high_cooling_sensitivity"],
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
                description=SYMBOLIC_DESCRIPTIONS["high_heating_sensitivity"],
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
                description=SYMBOLIC_DESCRIPTIONS["high_electricity_heating_change_point"],
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
                description=SYMBOLIC_DESCRIPTIONS["high_electricity_cooling_sensitivity"],
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
                description=SYMBOLIC_DESCRIPTIONS["high_electricity_heating_sensitivity"],
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
                description=SYMBOLIC_DESCRIPTIONS["high_fossil_fuel_baseload"],
                severity=_severity_gt(value, target),
                detected_value=value,
                threshold_value=target,
                metric="baseload",
            )
        )

    return symptoms


def map_symptoms_to_measures(symptoms: List[InefficiencySymptom]) -> List[EEMeasureRecommendation]:
    """Map detected symptoms to the top-level BETTER measures."""

    symptom_ids = {symptom.symptom_id for symptom in symptoms}
    recommendations: Dict[str, EEMeasureRecommendation] = {}

    def _add_measure(
        measure_token: str,
        triggers: Union[str, Iterable[str]],
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

    if "high_electricity_baseload" in symptom_ids or {
        "low_cooling_change_point",
        "high_heating_change_point",
    } & symptom_ids:
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
        triggers = envelope_group & symptom_ids
        _add_measure("DECREASE_INFILTRATION", triggers)
        _add_measure("ADD_WALL_CEILING_ROOF_INSULATION", triggers)
        _add_measure("UPGRADE_WINDOWS_TO_IMPROVE_THERMAL_EFFICIENCY", triggers)

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
    benchmark_input: Union[BenchmarkResult, Dict[str, Any]],
    *,
    building_type: Optional[BuildingSpaceType] = None,
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
