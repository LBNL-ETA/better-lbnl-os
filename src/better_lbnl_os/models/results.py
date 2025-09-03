"""Result models."""

from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from better_lbnl_os.models.building import BuildingData


class ChangePointModelResult(BaseModel):
    heating_slope: float | None = Field(None, description="Heating slope coefficient")
    heating_change_point: float | None = Field(None, description="Heating change point temperature")
    baseload: float = Field(..., description="Baseload consumption")
    cooling_change_point: float | None = Field(None, description="Cooling change point temperature")
    cooling_slope: float | None = Field(None, description="Cooling slope coefficient")
    r_squared: float = Field(..., ge=0, le=1, description="R-squared value")
    cvrmse: float = Field(..., ge=0, description="CV(RMSE) value")
    model_type: str = Field(..., description="Model type (1P, 3P-H, 3P-C, 5P)")
    heating_pvalue: float | None = Field(None, description="P-value for heating slope significance")
    cooling_pvalue: float | None = Field(None, description="P-value for cooling slope significance")

    def is_valid(self, min_r_squared: float = 0.6, max_cvrmse: float = 0.5) -> bool:
        return self.r_squared >= min_r_squared and self.cvrmse <= max_cvrmse

    def get_model_complexity(self) -> int:
        model_params = {"1P": 1, "3P-H": 3, "3P-C": 3, "5P": 5}
        return model_params.get(self.model_type, 1)

    def get_model_type_label(self, style: str = "short") -> str:
        short_to_long = {
            "1P": "1P",
            "3P-H": "3P Heating",
            "3P-C": "3P Cooling",
            "5P": "5P",
        }
        if style == "long":
            return short_to_long.get(self.model_type, self.model_type)
        return self.model_type

    def estimate_annual_consumption(self, annual_hdd: float, annual_cdd: float) -> float:
        annual = self.baseload * 365
        if self.heating_slope:
            annual += self.heating_slope * annual_hdd
        if self.cooling_slope:
            annual += self.cooling_slope * annual_cdd
        return annual


class BenchmarkResult(BaseModel):
    building_id: str = Field(..., description="Building identifier")
    percentile: float = Field(..., ge=0, le=100, description="Percentile ranking")
    z_score: float = Field(..., description="Statistical z-score")
    rating: str = Field(..., description="Performance rating")
    target_eui: float = Field(..., gt=0, description="Target EUI for improvement")
    median_eui: float = Field(..., gt=0, description="Median EUI for peer group")

    def get_rating_color(self) -> str:
        color_map = {
            "Excellent": "green",
            "Good": "lightgreen",
            "Average": "yellow",
            "Below Average": "orange",
            "Poor": "red",
        }
        return color_map.get(self.rating, "gray")

    def calculate_savings_potential(self, current_eui: float) -> float:
        if current_eui > 0:
            return max(0, (current_eui - self.target_eui) / current_eui * 100)
        return 0.0


class SavingsEstimate(BaseModel):
    energy_savings_kwh: float = Field(..., description="Annual energy savings in kWh")
    cost_savings_usd: float = Field(..., description="Annual cost savings in USD")
    emissions_savings_kg_co2: float = Field(..., description="Annual emissions savings in kg CO2")
    percent_reduction: float = Field(..., ge=0, le=100, description="Percentage reduction")

    def calculate_roi(self, investment_cost: float, discount_rate: float = 0.05) -> float:
        if investment_cost > 0:
            return (self.cost_savings_usd / investment_cost) * 100
        return 0.0

    def calculate_payback_period(self, investment_cost: float) -> float:
        if self.cost_savings_usd > 0:
            return investment_cost / self.cost_savings_usd
        return float("inf")


class EEMeasureRecommendation(BaseModel):
    measure_id: str = Field(..., description="Unique measure identifier")
    name: str = Field(..., description="Measure name")
    category: str = Field(..., description="Measure category")
    description: str = Field(..., description="Detailed description")
    estimated_savings: SavingsEstimate = Field(..., description="Estimated savings")
    confidence_level: str = Field(..., description="Confidence level (High/Medium/Low)")
    implementation_difficulty: str = Field(..., description="Implementation difficulty")

    def is_applicable(self, building: "BuildingData") -> bool:
        return True

    def prioritize_score(self) -> float:
        savings_score = min(self.estimated_savings.percent_reduction * 2, 50)
        difficulty_scores = {"Easy": 50, "Medium": 30, "Hard": 10}
        difficulty_score = difficulty_scores.get(self.implementation_difficulty, 20)
        confidence_multipliers = {"High": 1.0, "Medium": 0.8, "Low": 0.6}
        confidence_mult = confidence_multipliers.get(self.confidence_level, 0.7)
        return (savings_score + difficulty_score) * confidence_mult


__all__ = [
    "ChangePointModelResult",
    "BenchmarkResult",
    "SavingsEstimate",
    "EEMeasureRecommendation",
]
