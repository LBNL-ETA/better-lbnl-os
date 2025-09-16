"""Energy efficiency measure recommendations.

This module provides functions and models for generating energy efficiency
measure recommendations based on building performance analysis and benchmarking.
"""

from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from better_lbnl_os.core.savings import SavingsEstimate

if TYPE_CHECKING:
    from better_lbnl_os.models.building import BuildingData


class EEMeasureRecommendation(BaseModel):
    """Energy efficiency measure recommendation.

    Represents a specific energy efficiency improvement recommendation
    for a building, including estimated savings and implementation details.
    """
    measure_id: str = Field(..., description="Unique measure identifier")
    name: str = Field(..., description="Measure name")
    category: str = Field(..., description="Measure category")
    description: str = Field(..., description="Detailed description")
    estimated_savings: SavingsEstimate = Field(..., description="Estimated savings")
    confidence_level: str = Field(..., description="Confidence level (High/Medium/Low)")
    implementation_difficulty: str = Field(..., description="Implementation difficulty")

    def is_applicable(self, building: "BuildingData") -> bool:
        """Check if this measure is applicable to the given building.

        Args:
            building: Building data to check applicability against

        Returns:
            True if measure is applicable, False otherwise
        """
        # Default implementation - always applicable
        # Subclasses or specific implementations can override this
        return True

    def prioritize_score(self) -> float:
        """Calculate priority score for ranking recommendations.

        Returns:
            Priority score (higher is better priority)
        """
        # Base score on percent savings (up to 50 points)
        savings_score = min(self.estimated_savings.percent_reduction * 2, 50)

        # Score based on implementation difficulty
        difficulty_scores = {"Easy": 50, "Medium": 30, "Hard": 10}
        difficulty_score = difficulty_scores.get(self.implementation_difficulty, 20)

        # Apply confidence multiplier
        confidence_multipliers = {"High": 1.0, "Medium": 0.8, "Low": 0.6}
        confidence_mult = confidence_multipliers.get(self.confidence_level, 0.7)

        return (savings_score + difficulty_score) * confidence_mult

    def estimate_implementation_cost(self, building_floor_area: float) -> Optional[float]:
        """Estimate implementation cost based on building size.

        Args:
            building_floor_area: Building floor area in square feet

        Returns:
            Estimated cost in USD, or None if not estimable
        """
        # Default implementation returns None
        # Specific measure types can override with cost models
        return None


def generate_hvac_recommendations(
    heating_performance: str,
    cooling_performance: str,
    building_age: Optional[int] = None
) -> List[EEMeasureRecommendation]:
    """Generate HVAC-related recommendations based on performance ratings.

    Args:
        heating_performance: Heating performance rating (Good/Typical/Poor)
        cooling_performance: Cooling performance rating (Good/Typical/Poor)
        building_age: Optional building age in years

    Returns:
        List of HVAC recommendations
    """
    recommendations = []

    # Heating recommendations
    if heating_performance == "Poor":
        heating_savings = SavingsEstimate(
            energy_savings_kwh=5000,
            cost_savings_usd=600,
            emissions_savings_kg_co2=2000,
            percent_reduction=15.0
        )

        recommendations.append(EEMeasureRecommendation(
            measure_id="hvac_heating_upgrade",
            name="Heating System Upgrade",
            category="HVAC",
            description="Upgrade heating system to high-efficiency equipment",
            estimated_savings=heating_savings,
            confidence_level="High",
            implementation_difficulty="Medium"
        ))

    # Cooling recommendations
    if cooling_performance == "Poor":
        cooling_savings = SavingsEstimate(
            energy_savings_kwh=8000,
            cost_savings_usd=960,
            emissions_savings_kg_co2=3200,
            percent_reduction=20.0
        )

        recommendations.append(EEMeasureRecommendation(
            measure_id="hvac_cooling_upgrade",
            name="Cooling System Upgrade",
            category="HVAC",
            description="Upgrade cooling system to high-efficiency equipment",
            estimated_savings=cooling_savings,
            confidence_level="High",
            implementation_difficulty="Medium"
        ))

    # Age-based recommendations
    if building_age and building_age > 20:
        maintenance_savings = SavingsEstimate(
            energy_savings_kwh=3000,
            cost_savings_usd=360,
            emissions_savings_kg_co2=1200,
            percent_reduction=8.0
        )

        recommendations.append(EEMeasureRecommendation(
            measure_id="hvac_maintenance",
            name="HVAC System Maintenance",
            category="HVAC",
            description="Comprehensive HVAC system maintenance and tune-up",
            estimated_savings=maintenance_savings,
            confidence_level="Medium",
            implementation_difficulty="Easy"
        ))

    return recommendations


def generate_envelope_recommendations(
    baseload_performance: str,
    building_type: Optional[str] = None
) -> List[EEMeasureRecommendation]:
    """Generate building envelope recommendations based on baseload performance.

    Args:
        baseload_performance: Baseload performance rating (Good/Typical/Poor)
        building_type: Optional building type

    Returns:
        List of envelope recommendations
    """
    recommendations = []

    if baseload_performance == "Poor":
        insulation_savings = SavingsEstimate(
            energy_savings_kwh=6000,
            cost_savings_usd=720,
            emissions_savings_kg_co2=2400,
            percent_reduction=12.0
        )

        recommendations.append(EEMeasureRecommendation(
            measure_id="envelope_insulation",
            name="Building Insulation Upgrade",
            category="Envelope",
            description="Improve building envelope insulation",
            estimated_savings=insulation_savings,
            confidence_level="High",
            implementation_difficulty="Medium"
        ))

        windows_savings = SavingsEstimate(
            energy_savings_kwh=4000,
            cost_savings_usd=480,
            emissions_savings_kg_co2=1600,
            percent_reduction=8.0
        )

        recommendations.append(EEMeasureRecommendation(
            measure_id="envelope_windows",
            name="Window Replacement",
            category="Envelope",
            description="Install high-performance windows",
            estimated_savings=windows_savings,
            confidence_level="Medium",
            implementation_difficulty="Hard"
        ))

    return recommendations


def prioritize_recommendations(
    recommendations: List[EEMeasureRecommendation]
) -> List[EEMeasureRecommendation]:
    """Sort recommendations by priority score.

    Args:
        recommendations: List of recommendations to prioritize

    Returns:
        Sorted list with highest priority first
    """
    return sorted(recommendations, key=lambda r: r.prioritize_score(), reverse=True)


__all__ = [
    "EEMeasureRecommendation",
    "generate_hvac_recommendations",
    "generate_envelope_recommendations",
    "prioritize_recommendations",
]