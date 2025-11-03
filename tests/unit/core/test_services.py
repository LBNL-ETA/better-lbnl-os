from datetime import date
from types import SimpleNamespace

import pytest

from better_lbnl_os.core.savings import SavingsEstimate
from better_lbnl_os.core.services import BuildingAnalyticsService, PortfolioBenchmarkService
from better_lbnl_os.models import BuildingData, UtilityBillData, WeatherData


def _sample_building() -> BuildingData:
    return BuildingData(
        name="Sample Building",
        floor_area=50000,
        space_type="Office",
        location="Berkeley, CA",
    )


def _sample_utility_bills():
    return [
        UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 2, 1),
            consumption=1200,
            units="kWh",
            cost=150.0,
        )
    ]


def _sample_weather():
    return [
        WeatherData(
            station_id="TEST",
            latitude=37.87,
            longitude=-122.26,
            year=2024,
            month=1,
            avg_temp_c=12.3,
            min_temp_c=5.0,
            max_temp_c=18.0,
        )
    ]


def test_building_analytics_service_placeholders_return_defaults():
    service = BuildingAnalyticsService()
    building = _sample_building()
    bills = _sample_utility_bills()
    weather = _sample_weather()

    analysis = service.analyze_building(building, bills, weather)
    assert analysis["status"] == "success"
    assert analysis["building_id"] == building.name

    assert service.fit_models(building, bills, weather) == []

    benchmark_result = service.benchmark_building(building, [])
    assert benchmark_result.building_id == building.name

    savings = service.estimate_savings(building, benchmark_result, bills)
    assert isinstance(savings, SavingsEstimate)
    assert savings.energy_savings_kwh == 10000.0

    recommendations = service.recommend_measures(building, [], benchmark_result)
    assert recommendations == []


def test_portfolio_benchmark_service_aggregates_results():
    portfolio = PortfolioBenchmarkService()
    building = _sample_building()

    assert portfolio.calculate_portfolio_metrics() == {
        "status": "error",
        "message": "No buildings in portfolio",
    }

    result_a = SimpleNamespace(building_id="B1", percentile=40.0, rating="Average")
    result_b = SimpleNamespace(building_id="B2", percentile=80.0, rating="Good")

    portfolio.add_building(building, result_a)
    portfolio.add_building(building.model_copy(update={"name": "Second"}), result_b)

    metrics = portfolio.calculate_portfolio_metrics()
    assert metrics["total_buildings"] == 2
    assert metrics["average_percentile"] == pytest.approx(60.0, rel=1e-6)
    assert metrics["rating_distribution"] == {"Average": 1, "Good": 1}

    assert portfolio.identify_improvement_targets(1) == ["B2"]

    report = portfolio.generate_portfolio_report()
    assert report["metrics"] == metrics
    assert "report_date" in report
