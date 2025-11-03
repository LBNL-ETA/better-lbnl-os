"""Shared pytest fixtures for all tests.

This file provides common test fixtures that can be used across all test modules.
Fixtures defined here are automatically available to all tests.
"""

from datetime import date

import pytest

from better_lbnl_os.models import BuildingData, LocationInfo, UtilityBillData, WeatherData


@pytest.fixture
def sample_building():
    """Sample building data for testing."""
    return BuildingData(
        name="Test Office Building",
        floor_area=50000,
        space_type="Office",
        location="Berkeley, CA",
        country_code="US",
        climate_zone="3C",
    )


@pytest.fixture
def sample_electricity_bill():
    """Sample electricity bill for testing."""
    return UtilityBillData(
        fuel_type="ELECTRICITY",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        consumption=10000,
        units="kWh",
        cost=1500.0,
    )


@pytest.fixture
def sample_gas_bill():
    """Sample natural gas bill for testing."""
    return UtilityBillData(
        fuel_type="NATURAL_GAS",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        consumption=500,
        units="therms",
        cost=600.0,
    )


@pytest.fixture
def sample_location():
    """Sample location info for testing."""
    return LocationInfo(
        geo_lat=37.8716,
        geo_lng=-122.2727,
        zipcode="94709",
        state="CA",
        country_code="US",
        noaa_station_id="TEST001",
        noaa_station_name="Berkeley Test Station",
    )


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing."""
    return WeatherData(
        latitude=37.8716,
        longitude=-122.2727,
        year=2024,
        month=1,
        avg_temp_c=12.5,
        min_temp_c=8.0,
        max_temp_c=17.0,
        data_source="Test",
    )


@pytest.fixture
def sample_monthly_temps():
    """Sample monthly temperature data for a year (in Celsius)."""
    return [10.0, 11.5, 13.0, 15.5, 18.0, 21.0, 23.5, 23.0, 21.5, 18.0, 14.0, 11.0]


# Markers for test categorization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "network: marks tests that require network access")
