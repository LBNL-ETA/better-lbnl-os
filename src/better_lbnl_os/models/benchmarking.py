"""Benchmarking data models for energy performance analysis.

This module contains pure Python data structures for benchmarking building energy
performance against reference statistics. These models are framework-agnostic and
can be used with any data source (files, databases, APIs, etc.).
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class CoefficientBenchmarkStatistics(BaseModel):
    """Statistical data for a single change-point model coefficient.

    Used to represent the median and standard deviation of a coefficient
    across a reference dataset of buildings.
    """
    median: Optional[float] = Field(None, description="Median value of coefficient")
    stdev: Optional[float] = Field(None, description="Standard deviation of coefficient")


class EnergyTypeBenchmarkStatistics(BaseModel):
    """Benchmark statistics for all coefficients of one energy type."""
    heating_slope: Optional[CoefficientBenchmarkStatistics] = None
    heating_change_point: Optional[CoefficientBenchmarkStatistics] = None
    baseload: Optional[CoefficientBenchmarkStatistics] = None
    cooling_change_point: Optional[CoefficientBenchmarkStatistics] = None
    cooling_slope: Optional[CoefficientBenchmarkStatistics] = None


class BenchmarkStatistics(BaseModel):
    """Complete benchmark statistics for all energy types.

    This represents the statistical data derived from a reference dataset
    of buildings, used to benchmark individual buildings against.
    """
    ELECTRICITY: Optional[EnergyTypeBenchmarkStatistics] = None
    FOSSIL_FUEL: Optional[EnergyTypeBenchmarkStatistics] = None


class CoefficientBenchmarkResult(BaseModel):
    """Benchmarking result for a single coefficient.

    Contains the comparison of a building's coefficient value against
    reference statistics, including percentile ranking and performance rating.
    """
    coefficient_value: Optional[float] = Field(None, description="Original coefficient value")
    coefficient_value_with_area: Optional[float] = Field(None, description="Coefficient value scaled by floor area")
    rating: Optional[str] = Field(None, description="Performance rating (Good/Typical/Poor)")
    percentile: Optional[float] = Field(None, ge=0, le=100, description="Percentile ranking (0-100)")
    sample_median: Optional[float] = Field(None, description="Reference dataset median")
    sample_standard_deviation: Optional[float] = Field(None, description="Reference dataset standard deviation")
    conservative_level: Optional[float] = Field(None, description="Conservative target level")
    nominal_level: Optional[float] = Field(None, description="Nominal target level")
    aggressive_level: Optional[float] = Field(None, description="Aggressive target level")
    target_value: Optional[float] = Field(None, description="Target value for selected savings level")


class EnergyTypeBenchmarkResult(BaseModel):
    """Benchmark results for all coefficients of one energy type."""
    heating_slope: Optional[CoefficientBenchmarkResult] = None
    heating_change_point: Optional[CoefficientBenchmarkResult] = None
    baseload: Optional[CoefficientBenchmarkResult] = None
    cooling_change_point: Optional[CoefficientBenchmarkResult] = None
    cooling_slope: Optional[CoefficientBenchmarkResult] = None


class BenchmarkResult(BaseModel):
    """Complete benchmark results for a building.

    This represents the comparison of a single building's change-point model
    coefficients against reference statistics for all energy types.
    """
    building_id: Optional[str] = Field(None, description="Building identifier")
    floor_area: Optional[float] = Field(None, gt=0, description="Building floor area")
    savings_target: Optional[str] = Field(None, description="Savings target level used")
    ELECTRICITY: Optional[EnergyTypeBenchmarkResult] = None
    FOSSIL_FUEL: Optional[EnergyTypeBenchmarkResult] = None

    def get_overall_rating(self, energy_type: str = "ELECTRICITY") -> Optional[str]:
        """Get overall performance rating for an energy type.

        Args:
            energy_type: Energy type to get rating for ("ELECTRICITY" or "FOSSIL_FUEL")

        Returns:
            Overall rating string or None if no valid rating found
        """
        energy_result = getattr(self, energy_type, None)
        if not energy_result:
            return None

        # Get ratings from all coefficients
        ratings = []
        for coeff in ['baseload', 'heating_slope', 'cooling_slope']:
            coeff_result = getattr(energy_result, coeff, None)
            if coeff_result and coeff_result.rating:
                ratings.append(coeff_result.rating)

        if not ratings:
            return None

        # Simple majority vote
        rating_counts = {r: ratings.count(r) for r in set(ratings)}
        return max(rating_counts.items(), key=lambda x: x[1])[0]

    def get_average_percentile(self, energy_type: str = "ELECTRICITY") -> Optional[float]:
        """Get average percentile across all coefficients for an energy type.

        Args:
            energy_type: Energy type to analyze ("ELECTRICITY" or "FOSSIL_FUEL")

        Returns:
            Average percentile or None if no valid percentiles found
        """
        energy_result = getattr(self, energy_type, None)
        if not energy_result:
            return None

        percentiles = []
        for coeff in ['baseload', 'heating_slope', 'cooling_slope']:
            coeff_result = getattr(energy_result, coeff, None)
            if coeff_result and coeff_result.percentile is not None:
                percentiles.append(coeff_result.percentile)

        return sum(percentiles) / len(percentiles) if percentiles else None


__all__ = [
    "CoefficientBenchmarkStatistics",
    "EnergyTypeBenchmarkStatistics",
    "BenchmarkStatistics",
    "CoefficientBenchmarkResult",
    "EnergyTypeBenchmarkResult",
    "BenchmarkResult",
]