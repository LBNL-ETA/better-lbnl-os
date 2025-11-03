"""Unit tests for weather service."""

import unittest
from datetime import date
from unittest.mock import Mock

from better_lbnl_os.core.weather.interfaces import WeatherDataProvider
from better_lbnl_os.core.weather.service import WeatherService
from better_lbnl_os.models import LocationInfo, WeatherData, WeatherStation


class MockWeatherProvider(WeatherDataProvider):
    """Mock weather provider for testing."""

    def __init__(self):
        # Override methods with mocks at the instance level
        self.get_monthly_average = Mock()
        self.get_daily_temperatures = Mock()
        self.get_weather_data = Mock()
        self._get_nearest_station = Mock()
        self._validate_date_range = Mock(return_value=True)

    # Satisfy ABC requirements; these will be shadowed by instance mocks
    def get_monthly_average(self, latitude, longitude, year, month):  # type: ignore[override]
        raise NotImplementedError

    def get_daily_temperatures(self, latitude, longitude, start_date, end_date):  # type: ignore[override]
        raise NotImplementedError

    def get_weather_data(self, latitude, longitude, year, month):  # type: ignore[override]
        raise NotImplementedError

    def get_nearest_station(self, latitude, longitude, max_distance_km=100.0):
        return self._get_nearest_station(latitude, longitude, max_distance_km)

    def validate_date_range(self, start_date, end_date):
        return self._validate_date_range(start_date, end_date)

    def get_provider_name(self):
        return "Mock"

    def get_api_limits(self):
        return {"requests_per_day": 1000}


class TestWeatherService(unittest.TestCase):
    """Test weather service functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_provider = MockWeatherProvider()
        self.service = WeatherService(provider=self.mock_provider)

        self.location = LocationInfo(
            geo_lat=37.8716,
            geo_lng=-122.2727,
            zipcode="94709",
            state="CA",
            country_code="US",
            noaa_station_id="TEST001",
            noaa_station_name="Test Station",
        )

    def test_service_initialization(self):
        """Test service initialization."""
        # With custom provider
        self.assertEqual(self.service.provider, self.mock_provider)

        # Default provider (OpenMeteo)
        default_service = WeatherService()
        self.assertIsNotNone(default_service.provider)

    def test_get_provider_info(self):
        """Test getting provider information."""
        info = self.service.get_provider_info()

        self.assertEqual(info["name"], "Mock")
        self.assertEqual(info["limits"]["requests_per_day"], 1000)

    def test_validate_data_availability(self):
        """Test data availability validation."""
        # Test with end date
        result = self.service.validate_data_availability(date(2023, 1, 1), date(2023, 12, 31))
        self.assertTrue(result)
        self.mock_provider._validate_date_range.assert_called_once()

        # Test without end date (should use today)
        self.mock_provider._validate_date_range.reset_mock()
        result = self.service.validate_data_availability(date(2023, 1, 1))
        self.assertTrue(result)
        self.mock_provider._validate_date_range.assert_called_once()

    def test_find_nearest_station(self):
        """Test finding nearest station."""
        mock_station = WeatherStation(
            station_id="MOCK001",
            name="Mock Station",
            latitude=37.8,
            longitude=-122.3,
            distance_km=5.0,
        )
        self.mock_provider._get_nearest_station.return_value = mock_station

        station = self.service.find_nearest_station(37.8716, -122.2727)

        self.assertEqual(station, mock_station)
        self.mock_provider._get_nearest_station.assert_called_once_with(37.8716, -122.2727, 100.0)

    def test_get_weather_data_success(self):
        """Test successful weather data retrieval."""
        # Mock provider response
        mock_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2023,
            month=1,
            avg_temp_c=10.5,
            data_source="Mock",
        )
        self.mock_provider.get_weather_data.return_value = mock_weather

        # Call sync method
        weather = self.service.get_weather_data(self.location, 2023, 1)

        # Verify result
        self.assertIsNotNone(weather)
        self.assertEqual(weather.avg_temp_c, 10.5)
        self.assertEqual(weather.station_id, "TEST001")  # Should be set from location

        # Verify provider was called
        self.mock_provider.get_weather_data.assert_called_once_with(37.8716, -122.2727, 2023, 1)

    def test_get_weather_data_invalid_location(self):
        """Test weather data retrieval with invalid location."""
        # Invalid location
        invalid_location = LocationInfo(
            geo_lat=200, geo_lng=-122.2727, zipcode="00000", state="XX"  # Invalid latitude
        )

        weather = self.service.get_weather_data(invalid_location, 2023, 1)

        # Should return None for invalid location
        self.assertIsNone(weather)
        self.mock_provider.get_weather_data.assert_not_called()

    def test_get_weather_range(self):
        """Test getting weather for a date range."""
        # Mock provider responses
        mock_weathers = [
            WeatherData(
                latitude=37.8716,
                longitude=-122.2727,
                year=2023,
                month=month,
                avg_temp_c=10.0 + month,
                data_source="Mock",
            )
            for month in range(1, 4)
        ]
        self.mock_provider.get_weather_data.side_effect = mock_weathers

        weathers = self.service.get_weather_range(self.location, 2023, 1, 2023, 3)

        # Verify result
        self.assertEqual(len(weathers), 3)
        self.assertEqual(weathers[0].month, 1)
        self.assertEqual(weathers[1].month, 2)
        self.assertEqual(weathers[2].month, 3)

        # Verify provider was called 3 times
        self.assertEqual(self.mock_provider.get_weather_data.call_count, 3)

    def test_fill_missing_weather(self):
        """Test filling missing weather data."""
        # Existing data for months 1 and 3
        existing_data = [
            WeatherData(
                latitude=37.8716,
                longitude=-122.2727,
                year=2023,
                month=1,
                avg_temp_c=10.0,
                data_source="Existing",
            ),
            WeatherData(
                latitude=37.8716,
                longitude=-122.2727,
                year=2023,
                month=3,
                avg_temp_c=14.0,
                data_source="Existing",
            ),
        ]

        # Mock provider to return data for month 2
        mock_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2023,
            month=2,
            avg_temp_c=12.0,
            data_source="Mock",
        )
        self.mock_provider.get_weather_data.return_value = mock_weather

        filled = self.service.fill_missing_weather(
            self.location, 2023, 1, 2023, 3, existing_data=existing_data
        )

        # Verify result
        self.assertEqual(len(filled), 3)
        # Should be sorted by month
        self.assertEqual(filled[0].month, 1)
        self.assertEqual(filled[1].month, 2)
        self.assertEqual(filled[2].month, 3)

        # Verify only month 2 was fetched
        self.mock_provider.get_weather_data.assert_called_once_with(37.8716, -122.2727, 2023, 2)


if __name__ == "__main__":
    unittest.main()
