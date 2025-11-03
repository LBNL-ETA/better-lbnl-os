"""Core benchmarking engine for building energy performance analysis.

This module provides pure, framework-agnostic functions for benchmarking building
energy performance against reference statistics. It handles the comparison of
change-point model coefficients and provides performance ratings and targets.
"""

import logging

import numpy as np

from better_lbnl_os.constants.building_types import BuildingSpaceType
from better_lbnl_os.core.changepoint import ChangePointModelResult
from better_lbnl_os.models.benchmarking import (
    BenchmarkResult,
    BenchmarkStatistics,
    CoefficientBenchmarkResult,
    EnergyTypeBenchmarkResult,
    EnergyTypeBenchmarkStatistics,
)
from better_lbnl_os.utils.statistics import (
    assign_performance_rating,
    calculate_coefficient_statistics,
    calculate_percentile_from_z_score,
    calculate_z_score,
)

logger = logging.getLogger(__name__)


def create_statistics_from_models(
    change_point_models: list[ChangePointModelResult], building_ids: list[str] | None = None
) -> BenchmarkStatistics:
    """Create benchmark statistics from a collection of change-point models.

    Args:
        change_point_models: List of fitted change-point models
        building_ids: Optional list of building identifiers for logging

    Returns:
        BenchmarkStatistics with median and standard deviation for each coefficient

    Raises:
        ValueError: If no valid models provided
    """
    if not change_point_models:
        raise ValueError("At least one change-point model must be provided")

    # Collect coefficient values by energy type
    electricity_coeffs = {
        "heating_slope": [],
        "heating_change_point": [],
        "baseload": [],
        "cooling_change_point": [],
        "cooling_slope": [],
    }

    fossil_fuel_coeffs = {
        "heating_slope": [],
        "heating_change_point": [],
        "baseload": [],
        "cooling_change_point": [],
        "cooling_slope": [],
    }

    # Extract coefficients from each model
    for i, model in enumerate(change_point_models):
        building_ids[i] if building_ids and i < len(building_ids) else f"building_{i}"

        # For simplicity, assume ELECTRICITY models have cooling dominance
        # and FOSSIL_FUEL models have heating dominance
        # In real implementation, this would be determined by model type or other criteria

        if model.cooling_slope is not None and model.cooling_slope > 0:
            # Treat as electricity model
            electricity_coeffs["heating_slope"].append(model.heating_slope)
            electricity_coeffs["heating_change_point"].append(model.heating_change_point)
            electricity_coeffs["baseload"].append(model.baseload)
            electricity_coeffs["cooling_change_point"].append(model.cooling_change_point)
            electricity_coeffs["cooling_slope"].append(model.cooling_slope)

        if model.heating_slope is not None and model.heating_slope < 0:
            # Treat as fossil fuel model
            fossil_fuel_coeffs["heating_slope"].append(model.heating_slope)
            fossil_fuel_coeffs["heating_change_point"].append(model.heating_change_point)
            fossil_fuel_coeffs["baseload"].append(model.baseload)
            fossil_fuel_coeffs["cooling_change_point"].append(model.cooling_change_point)
            fossil_fuel_coeffs["cooling_slope"].append(model.cooling_slope)

    # Create statistics for each energy type
    electricity_stats = EnergyTypeBenchmarkStatistics(
        heating_slope=calculate_coefficient_statistics(electricity_coeffs["heating_slope"]),
        heating_change_point=calculate_coefficient_statistics(
            electricity_coeffs["heating_change_point"]
        ),
        baseload=calculate_coefficient_statistics(electricity_coeffs["baseload"]),
        cooling_change_point=calculate_coefficient_statistics(
            electricity_coeffs["cooling_change_point"]
        ),
        cooling_slope=calculate_coefficient_statistics(electricity_coeffs["cooling_slope"]),
    )

    fossil_fuel_stats = EnergyTypeBenchmarkStatistics(
        heating_slope=calculate_coefficient_statistics(fossil_fuel_coeffs["heating_slope"]),
        heating_change_point=calculate_coefficient_statistics(
            fossil_fuel_coeffs["heating_change_point"]
        ),
        baseload=calculate_coefficient_statistics(fossil_fuel_coeffs["baseload"]),
        cooling_change_point=calculate_coefficient_statistics(
            fossil_fuel_coeffs["cooling_change_point"]
        ),
        cooling_slope=calculate_coefficient_statistics(fossil_fuel_coeffs["cooling_slope"]),
    )

    return BenchmarkStatistics(ELECTRICITY=electricity_stats, FOSSIL_FUEL=fossil_fuel_stats)


def get_target_coefficient_value(
    coefficient_name: str,
    current_value: float,
    median: float,
    stdev: float,
    savings_target: str = "NOMINAL",
) -> float:
    """Calculate target coefficient value based on savings target level.

    Args:
        coefficient_name: Name of the coefficient
        current_value: Current coefficient value
        median: Reference median
        stdev: Reference standard deviation
        savings_target: Target level ("CONSERVATIVE", "NOMINAL", "AGGRESSIVE")

    Returns:
        Target coefficient value
    """
    # For coefficients where larger values are better
    if coefficient_name in ["cooling_change_point", "heating_slope"]:
        if savings_target == "CONSERVATIVE":
            target = median - stdev
        elif savings_target == "NOMINAL":
            target = median
        else:  # AGGRESSIVE
            target = median + stdev / 2
        # Don't suggest worse performance than current
        return max(current_value, target)

    # For coefficients where smaller values are better
    else:
        if savings_target == "CONSERVATIVE":
            target = median + stdev
        elif savings_target == "NOMINAL":
            target = median
        else:  # AGGRESSIVE
            target = median - stdev / 2
        # Don't suggest worse performance than current
        return min(current_value, target)


def benchmark_coefficient(
    coefficient_name: str,
    coefficient_value: float | None,
    median: float | None,
    stdev: float | None,
    savings_target: str,
    floor_area: float,
) -> CoefficientBenchmarkResult:
    """Benchmark a single coefficient against reference statistics.

    Args:
        coefficient_name: Name of the coefficient
        coefficient_value: Current coefficient value
        median: Reference median
        stdev: Reference standard deviation
        savings_target: Savings target level
        floor_area: Building floor area

    Returns:
        CoefficientBenchmarkResult with comparison metrics
    """
    logger.debug(
        f"Benchmarking {coefficient_name}: value={coefficient_value}, "
        f"median={median}, stdev={stdev}"
    )

    result = CoefficientBenchmarkResult(
        coefficient_value=coefficient_value,
        coefficient_value_with_area=coefficient_value * floor_area if coefficient_value else None,
        sample_median=median,
        sample_standard_deviation=stdev,
    )

    # Return early if we don't have enough data
    if any(x is None for x in [coefficient_value, median, stdev]):
        return result

    # Calculate z-score and percentile
    z_score = calculate_z_score(coefficient_value, median, stdev)

    # For coefficients where larger values are better (cooling_change_point, heating_slope)
    # reverse the z-score for percentile calculation
    if coefficient_name in ["cooling_change_point", "heating_slope"]:
        percentile = calculate_percentile_from_z_score(z_score)
        # For rating, use negative z-score (higher values = better performance = negative z-score for rating)
        rating_z_score = -z_score

        # Calculate target levels
        conservative_level = median - stdev
        nominal_level = median
        aggressive_level = median + stdev / 2
    else:
        # For other coefficients, smaller values are better
        percentile = calculate_percentile_from_z_score(-z_score)
        rating_z_score = z_score

        # Calculate target levels
        conservative_level = median + stdev
        nominal_level = median
        aggressive_level = median - stdev / 2

    # Assign performance rating
    rating = assign_performance_rating(rating_z_score)

    # Calculate target value
    target_value = get_target_coefficient_value(
        coefficient_name, coefficient_value, median, stdev, savings_target
    )

    # Update result
    result.percentile = percentile
    result.rating = rating
    result.conservative_level = conservative_level
    result.nominal_level = nominal_level
    result.aggressive_level = aggressive_level
    result.target_value = target_value

    return result


def benchmark_building(
    change_point_results: dict[str, ChangePointModelResult],
    benchmark_statistics: BenchmarkStatistics,
    floor_area: float,
    savings_target: str = "NOMINAL",
    building_id: str | None = None,
) -> BenchmarkResult:
    """Benchmark a building's change-point models against reference statistics.

    Args:
        change_point_results: Dictionary mapping energy types to change-point results
        benchmark_statistics: Reference statistics to compare against
        floor_area: Building floor area
        savings_target: Savings target level ("CONSERVATIVE", "NOMINAL", "AGGRESSIVE")
        building_id: Optional building identifier

    Returns:
        BenchmarkResult with complete comparison metrics

    Raises:
        ValueError: If required inputs are missing
    """
    if not change_point_results:
        raise ValueError("At least one change-point result must be provided")

    if not benchmark_statistics:
        raise ValueError("Benchmark statistics must be provided")

    if floor_area <= 0:
        raise ValueError("Floor area must be positive")

    logger.info(f"Benchmarking building {building_id or 'unknown'}")

    result = BenchmarkResult(
        building_id=building_id, floor_area=floor_area, savings_target=savings_target
    )

    # Benchmark each energy type
    for energy_type, cp_result in change_point_results.items():
        if energy_type not in ["ELECTRICITY", "FOSSIL_FUEL"]:
            logger.warning(f"Unknown energy type: {energy_type}")
            continue

        # Get benchmark statistics for this energy type
        energy_stats = getattr(benchmark_statistics, energy_type, None)
        if not energy_stats:
            logger.warning(f"No benchmark statistics for {energy_type}")
            continue

        # Create energy type result
        energy_result = EnergyTypeBenchmarkResult()

        # Benchmark each coefficient
        coefficients = {
            "heating_slope": cp_result.heating_slope,
            "heating_change_point": cp_result.heating_change_point,
            "baseload": cp_result.baseload,
            "cooling_change_point": cp_result.cooling_change_point,
            "cooling_slope": cp_result.cooling_slope,
        }

        for coeff_name, coeff_value in coefficients.items():
            # Get reference statistics for this coefficient
            coeff_stats = getattr(energy_stats, coeff_name, None)
            if not coeff_stats:
                continue

            # Benchmark the coefficient
            coeff_result = benchmark_coefficient(
                coefficient_name=coeff_name,
                coefficient_value=coeff_value,
                median=coeff_stats.median,
                stdev=coeff_stats.stdev,
                savings_target=savings_target,
                floor_area=floor_area,
            )

            # Store result
            setattr(energy_result, coeff_name, coeff_result)

        # Store energy type result
        setattr(result, energy_type, energy_result)

    return result


def calculate_portfolio_statistics(building_results: list[BenchmarkResult]) -> dict[str, float]:
    """Calculate portfolio-level statistics from individual building results.

    Args:
        building_results: List of benchmark results for buildings in portfolio

    Returns:
        Dictionary with portfolio-level metrics
    """
    if not building_results:
        return {}

    stats = {
        "total_buildings": len(building_results),
        "total_floor_area": sum(r.floor_area for r in building_results if r.floor_area),
    }

    # Calculate performance distribution
    for energy_type in ["ELECTRICITY", "FOSSIL_FUEL"]:
        ratings = []
        percentiles = []

        for result in building_results:
            overall_rating = result.get_overall_rating(energy_type)
            if overall_rating:
                ratings.append(overall_rating)

            avg_percentile = result.get_average_percentile(energy_type)
            if avg_percentile is not None:
                percentiles.append(avg_percentile)

        if ratings:
            stats[f"{energy_type.lower()}_ratings"] = {
                "Good": ratings.count("Good"),
                "Typical": ratings.count("Typical"),
                "Poor": ratings.count("Poor"),
            }

        if percentiles:
            stats[f"{energy_type.lower()}_avg_percentile"] = np.mean(percentiles)

    return stats


# Global loader instance for convenience
_default_loader = None


def get_reference_statistics(
    country_code: str, building_type: str | BuildingSpaceType, custom_data_path: str | None = None
) -> BenchmarkStatistics | None:
    """Get reference statistics for benchmarking.

    Args:
        country_code: ISO country code (e.g., 'US', 'MX')
        building_type: Building type enum or string
        custom_data_path: Optional path to custom JSON manifest

    Returns:
        BenchmarkStatistics if available, None otherwise
    """
    from better_lbnl_os.data.loader import ReferenceStatisticsLoader

    global _default_loader
    if custom_data_path or _default_loader is None:
        loader = ReferenceStatisticsLoader(custom_data_path)
        if not custom_data_path:
            _default_loader = loader
    else:
        loader = _default_loader

    if isinstance(building_type, str):
        try:
            building_type = BuildingSpaceType.from_benchmark_id(building_type)
        except ValueError:
            logger.error(f"Invalid building type: {building_type}")
            return None

    return loader.get_statistics(country_code, building_type)


def benchmark_with_reference(
    change_point_results: dict[str, ChangePointModelResult],
    floor_area: float,
    country_code: str,
    building_type: str | BuildingSpaceType,
    custom_statistics_path: str | None = None,
    savings_target: str = "NOMINAL",
    building_id: str | None = None,
) -> BenchmarkResult:
    """Benchmark building using reference statistics.

    Allows using either built-in statistics or custom data.

    Args:
        change_point_results: Dictionary mapping energy types to change-point results
        floor_area: Building floor area
        country_code: ISO country code (e.g., 'US', 'MX')
        building_type: Building type enum or string
        custom_statistics_path: Optional path to custom JSON manifest
        savings_target: Savings target level ("CONSERVATIVE", "NOMINAL", "AGGRESSIVE")
        building_id: Optional building identifier

    Returns:
        BenchmarkResult with complete comparison metrics

    Raises:
        ValueError: If no reference statistics are available or inputs are invalid
    """
    statistics = get_reference_statistics(country_code, building_type, custom_statistics_path)
    if not statistics:
        raise ValueError(f"No reference statistics available for {country_code}/{building_type}")

    return benchmark_building(
        change_point_results, statistics, floor_area, savings_target, building_id
    )


def list_available_reference_statistics(
    custom_data_path: str | None = None,
) -> list[tuple[str, BuildingSpaceType]]:
    """List all available reference statistics.

    Args:
        custom_data_path: Optional path to custom JSON manifest

    Returns:
        List of (country_code, building_type) tuples
    """
    from better_lbnl_os.data.loader import ReferenceStatisticsLoader

    loader = ReferenceStatisticsLoader(custom_data_path)
    return loader.list_available()


__all__ = [
    "benchmark_building",
    "benchmark_coefficient",
    "benchmark_with_reference",
    "calculate_portfolio_statistics",
    "create_statistics_from_models",
    "get_reference_statistics",
    "get_target_coefficient_value",
    "list_available_reference_statistics",
]
