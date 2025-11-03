"""Core services for orchestrating building energy analytics workflows (moved)."""

from better_lbnl_os.core.changepoint import ChangePointModelResult
from better_lbnl_os.core.recommendations import EEMeasureRecommendation
from better_lbnl_os.core.savings import SavingsEstimate
from better_lbnl_os.models import (
    BuildingData,
    UtilityBillData,
    WeatherData,
)
from better_lbnl_os.models.benchmarking import BenchmarkResult


class BuildingAnalyticsService:
    """Service for orchestrating building energy analysis workflows."""

    def analyze_building(
        self,
        building: BuildingData,
        utility_bills: list[UtilityBillData],
        weather_data: list[WeatherData],
    ) -> dict:
        # Placeholder implementation
        return {
            "status": "success",
            "building_id": building.name,
            "message": "Analysis service to be implemented",
        }

    def fit_models(
        self,
        building: BuildingData,
        utility_bills: list[UtilityBillData],
        weather_data: list[WeatherData],
    ) -> list[ChangePointModelResult]:
        # Placeholder - will integrate with core algorithms
        return []

    def benchmark_building(
        self,
        building: BuildingData,
        model_results: list[ChangePointModelResult],
    ) -> BenchmarkResult:
        # Placeholder - will implement benchmarking logic
        return BenchmarkResult(
            building_id=building.name,
            percentile=50.0,
            z_score=0.0,
            rating="Average",
            target_eui=100.0,
            median_eui=100.0,
        )

    def estimate_savings(
        self,
        building: BuildingData,
        benchmark_result: BenchmarkResult,
        utility_bills: list[UtilityBillData],
    ) -> SavingsEstimate:
        # Placeholder - will implement savings calculation
        return SavingsEstimate(
            energy_savings_kwh=10000.0,
            cost_savings_usd=1000.0,
            emissions_savings_kg_co2=5000.0,
            percent_reduction=15.0,
        )

    def recommend_measures(
        self,
        building: BuildingData,
        model_results: list[ChangePointModelResult],
        benchmark_result: BenchmarkResult,
    ) -> list[EEMeasureRecommendation]:
        # Placeholder - will implement recommendation engine
        return []


class PortfolioBenchmarkService:
    """Service for portfolio-level benchmarking and analysis."""

    def __init__(self):
        self.buildings: list[BuildingData] = []
        self.results: list[BenchmarkResult] = []

    def add_building(self, building: BuildingData, benchmark_result: BenchmarkResult) -> None:
        self.buildings.append(building)
        self.results.append(benchmark_result)

    def calculate_portfolio_metrics(self) -> dict:
        if not self.results:
            return {"status": "error", "message": "No buildings in portfolio"}
        avg_percentile = sum(r.percentile for r in self.results) / len(self.results)
        rating_counts: dict[str, int] = {}
        for result in self.results:
            rating_counts[result.rating] = rating_counts.get(result.rating, 0) + 1
        return {
            "total_buildings": len(self.buildings),
            "average_percentile": avg_percentile,
            "rating_distribution": rating_counts,
        }

    def identify_improvement_targets(self, top_n: int = 10) -> list[str]:
        sorted_results = sorted(self.results, key=lambda r: r.percentile, reverse=True)
        return [r.building_id for r in sorted_results[:top_n]]

    def generate_portfolio_report(self) -> dict:
        metrics = self.calculate_portfolio_metrics()
        targets = self.identify_improvement_targets()
        return {
            "metrics": metrics,
            "improvement_targets": targets,
            "report_date": "2025-01-21",
        }
