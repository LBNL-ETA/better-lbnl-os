"""Unit tests for batch weather fetching optimization."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from better_lbnl_os.core.weather.providers.open_meteo import OpenMeteoProvider
from better_lbnl_os.core.weather.service import WeatherService
from better_lbnl_os.models import LocationInfo, WeatherData


class TestBatchWeatherFetching(unittest.TestCase):
    """Test batch weather fetching functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.location = LocationInfo(
            geo_lat=37.8716, geo_lng=-122.2727, zipcode="94709", state="CA", country_code="US"
        )

    @patch("better_lbnl_os.core.weather.providers.open_meteo.requests.get")
    def test_openmeteo_batch_fetching(self, mock_get):
        """Test that OpenMeteo provider can fetch multiple months in one request."""
        # Mock the API response for a batch request
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hourly": {
                "time": [
                    f"2024-0{month}-{day:02d}T{hour:02d}:00"
                    for month in range(1, 4)
                    for day in range(1, 29)
                    for hour in range(24)
                ],
                "temperature_2m": [
                    10.0 + month + (hour * 0.1)
                    for month in range(1, 4)
                    for day in range(1, 29)
                    for hour in range(24)
                ],
            },
            "daily": {
                "time": [
                    f"2024-0{month}-{day:02d}" for month in range(1, 4) for day in range(1, 29)
                ],
                "temperature_2m_min": [5.0 + month for month in range(1, 4) for _ in range(28)],
                "temperature_2m_max": [15.0 + month for month in range(1, 4) for _ in range(28)],
                "temperature_2m_mean": [10.0 + month for month in range(1, 4) for _ in range(28)],
            },
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create provider and call batch method
        provider = OpenMeteoProvider(api_key="test_key")
        weather_list = provider.get_weather_data_batch(
            latitude=37.8716,
            longitude=-122.2727,
            start_year=2024,
            start_month=1,
            end_year=2024,
            end_month=3,
        )

        # Verify results
        self.assertEqual(len(weather_list), 3, "Should return 3 months of data")
        self.assertEqual(weather_list[0].month, 1)
        self.assertEqual(weather_list[1].month, 2)
        self.assertEqual(weather_list[2].month, 3)

        # Verify only ONE API call was made
        self.assertEqual(mock_get.call_count, 1, "Should make only one API call")

        # Verify the API call parameters
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["start_date"], "2024-01-01")
        self.assertEqual(params["end_date"], "2024-03-31")

    @patch("better_lbnl_os.core.weather.providers.open_meteo.requests.get")
    def test_service_uses_batch_when_available(self, mock_get):
        """Test that WeatherService uses batch method when provider supports it."""
        # Mock batch response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hourly": {
                "time": [
                    f"2024-01-{day:02d}T{hour:02d}:00" for day in range(1, 29) for hour in range(24)
                ],
                "temperature_2m": [10.0 for _ in range(28 * 24)],
            },
            "daily": {
                "time": [f"2024-01-{day:02d}" for day in range(1, 29)],
                "temperature_2m_min": [5.0 for _ in range(28)],
                "temperature_2m_max": [15.0 for _ in range(28)],
                "temperature_2m_mean": [10.0 for _ in range(28)],
            },
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create service with OpenMeteo provider
        provider = OpenMeteoProvider(api_key="test_key")
        service = WeatherService(provider=provider)

        # Get weather range
        weather_data = service.get_weather_range(
            self.location, start_year=2024, start_month=1, end_year=2024, end_month=1
        )

        # Verify batch was used (only 1 API call)
        self.assertEqual(len(weather_data), 1)
        self.assertEqual(mock_get.call_count, 1)

    def test_batch_method_fallback(self):
        """Test that service falls back to month-by-month if batch fails."""
        # Create a mock provider that doesn't support batch
        mock_provider = Mock()
        mock_provider.get_weather_data_batch.return_value = []  # Batch not supported

        # Mock month-by-month responses
        mock_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=1,
            avg_temp_c=10.5,
            data_source="Mock",
        )
        mock_provider.get_weather_data.return_value = mock_weather

        service = WeatherService(provider=mock_provider)

        # Get weather range
        weather_data = service.get_weather_range(
            self.location, start_year=2024, start_month=1, end_year=2024, end_month=2
        )

        # Verify it fell back to month-by-month (2 calls)
        self.assertEqual(len(weather_data), 2)
        self.assertEqual(mock_provider.get_weather_data.call_count, 2)


if __name__ == "__main__":
    unittest.main()
