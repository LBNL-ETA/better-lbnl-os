"""Energy savings estimation for building performance analysis.

This module provides functions and models for calculating energy savings
potential based on building change-point models and benchmark comparisons.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class SavingsEstimate(BaseModel):
    """Estimated energy savings from efficiency improvements.

    Represents the calculated savings potential for a building based on
    change-point model analysis and benchmarking against peer buildings.
    """
    energy_savings_kwh: float = Field(..., description="Annual energy savings in kWh")
    cost_savings_usd: float = Field(..., description="Annual cost savings in USD")
    emissions_savings_kg_co2: float = Field(..., description="Annual emissions savings in kg CO2")
    percent_reduction: float = Field(..., ge=0, le=100, description="Percentage reduction")

    def calculate_roi(self, investment_cost: float, discount_rate: float = 0.05) -> float:
        """Calculate return on investment percentage.

        Args:
            investment_cost: Upfront investment cost in USD
            discount_rate: Annual discount rate (default 5%)

        Returns:
            ROI as percentage
        """
        if investment_cost > 0:
            return (self.cost_savings_usd / investment_cost) * 100
        return 0.0

    def calculate_payback_period(self, investment_cost: float) -> float:
        """Calculate simple payback period in years.

        Args:
            investment_cost: Upfront investment cost in USD

        Returns:
            Payback period in years (or infinity if no savings)
        """
        if self.cost_savings_usd > 0:
            return investment_cost / self.cost_savings_usd
        return float("inf")

    def calculate_net_present_value(
        self,
        investment_cost: float,
        project_lifetime: int = 20,
        discount_rate: float = 0.05
    ) -> float:
        """Calculate net present value of the savings.

        Args:
            investment_cost: Upfront investment cost in USD
            project_lifetime: Project lifetime in years (default 20)
            discount_rate: Annual discount rate (default 5%)

        Returns:
            Net present value in USD
        """
        if discount_rate <= 0:
            return self.cost_savings_usd * project_lifetime - investment_cost

        # Calculate present value of annual savings
        pv_factor = (1 - (1 + discount_rate) ** -project_lifetime) / discount_rate
        pv_savings = self.cost_savings_usd * pv_factor

        return pv_savings - investment_cost


def calculate_savings_from_targets(
    current_consumption: float,
    target_consumption: float,
    energy_price_per_kwh: float = 0.12,
    emissions_factor_kg_co2_per_kwh: float = 0.4
) -> SavingsEstimate:
    """Calculate savings estimate from current and target consumption.

    Args:
        current_consumption: Current annual energy consumption in kWh
        target_consumption: Target annual energy consumption in kWh
        energy_price_per_kwh: Energy price in USD per kWh (default $0.12)
        emissions_factor_kg_co2_per_kwh: Emissions factor (default 0.4 kg CO2/kWh)

    Returns:
        SavingsEstimate with calculated values

    Raises:
        ValueError: If current consumption is not positive
    """
    if current_consumption <= 0:
        raise ValueError("Current consumption must be positive")

    energy_savings_kwh = max(0, current_consumption - target_consumption)
    cost_savings_usd = energy_savings_kwh * energy_price_per_kwh
    emissions_savings_kg_co2 = energy_savings_kwh * emissions_factor_kg_co2_per_kwh
    percent_reduction = (energy_savings_kwh / current_consumption) * 100

    return SavingsEstimate(
        energy_savings_kwh=energy_savings_kwh,
        cost_savings_usd=cost_savings_usd,
        emissions_savings_kg_co2=emissions_savings_kg_co2,
        percent_reduction=percent_reduction
    )


def calculate_savings_from_coefficients(
    current_coefficients: Dict[str, float],
    target_coefficients: Dict[str, float],
    annual_hdd: float,
    annual_cdd: float,
    energy_price_per_kwh: float = 0.12,
    emissions_factor_kg_co2_per_kwh: float = 0.4
) -> SavingsEstimate:
    """Calculate savings from change-point model coefficient improvements.

    Args:
        current_coefficients: Current model coefficients
        target_coefficients: Target model coefficients
        annual_hdd: Annual heating degree days
        annual_cdd: Annual cooling degree days
        energy_price_per_kwh: Energy price in USD per kWh
        emissions_factor_kg_co2_per_kwh: Emissions factor

    Returns:
        SavingsEstimate based on coefficient improvements
    """
    # Calculate current annual consumption
    current_annual = current_coefficients.get('baseload', 0) * 365
    if current_coefficients.get('heating_slope'):
        current_annual += current_coefficients['heating_slope'] * annual_hdd
    if current_coefficients.get('cooling_slope'):
        current_annual += current_coefficients['cooling_slope'] * annual_cdd

    # Calculate target annual consumption
    target_annual = target_coefficients.get('baseload', 0) * 365
    if target_coefficients.get('heating_slope'):
        target_annual += target_coefficients['heating_slope'] * annual_hdd
    if target_coefficients.get('cooling_slope'):
        target_annual += target_coefficients['cooling_slope'] * annual_cdd

    return calculate_savings_from_targets(
        current_consumption=current_annual,
        target_consumption=target_annual,
        energy_price_per_kwh=energy_price_per_kwh,
        emissions_factor_kg_co2_per_kwh=emissions_factor_kg_co2_per_kwh
    )


__all__ = [
    "SavingsEstimate",
    "calculate_savings_from_targets",
    "calculate_savings_from_coefficients",
]