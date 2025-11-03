"""Unit tests for weather data providers."""

import unittest
from datetime import date, datetime
from unittest.mock import Mock, patch

from better_lbnl_os.core.weather.providers import NOAAProvider, OpenMeteoProvider


class TestOpenMeteoProvider(unittest.TestCase):
    """Test OpenMeteo weather provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = OpenMeteoProvider()
        self.provider_with_key = OpenMeteoProvider(api_key="test_key")

    def test_provider_initialization(self):
        """Test provider initialization with and without API key."""
        # Without API key - should use free tier
        self.assertIsNone(self.provider.api_key)
        self.assertEqual(self.provider.base_url, "https://archive-api.open-meteo.com/v1/archive")

        # With API key - should use commercial tier
        self.assertEqual(self.provider_with_key.api_key, "test_key")
        self.assertEqual(
            self.provider_with_key.base_url,
            "https://customer-archive-api.open-meteo.com/v1/archive",
        )

    def test_validate_date_range(self):
        """Test date range validation."""
        # Valid date range
        self.assertTrue(self.provider.validate_date_range(date(2023, 1, 1), date(2023, 12, 31)))

        # Future date - invalid
        future_date = datetime.now().date().replace(year=datetime.now().year + 1)
        self.assertFalse(self.provider.validate_date_range(date(2023, 1, 1), future_date))

        # Too old - invalid
        self.assertFalse(self.provider.validate_date_range(date(1930, 1, 1), date(1930, 12, 31)))

        # Date range too long - invalid
        self.assertFalse(
            self.provider.validate_date_range(
                date(2020, 1, 1), date(2022, 12, 31)  # More than 365 days
            )
        )

    def test_get_nearest_station(self):
        """Test getting nearest station (virtual for OpenMeteo)."""
        station = self.provider.get_nearest_station(37.8716, -122.2727)

        self.assertIsNotNone(station)
        self.assertEqual(station.latitude, 37.8716)
        self.assertEqual(station.longitude, -122.2727)
        self.assertEqual(station.distance_km, 0.0)
        self.assertEqual(station.data_source, "OpenMeteo")
        self.assertIn("Grid Point", station.name)

    def test_get_api_limits(self):
        """Test API limit information."""
        # Free tier limits
        free_limits = self.provider.get_api_limits()
        self.assertEqual(free_limits["requests_per_hour"], 1000)
        self.assertEqual(free_limits["requests_per_day"], 10000)
        self.assertEqual(free_limits["max_date_range_days"], 365)
        self.assertTrue(free_limits["historical_data_available"])

        # Commercial tier limits
        paid_limits = self.provider_with_key.get_api_limits()
        self.assertEqual(paid_limits["requests_per_hour"], 10000)
        self.assertEqual(paid_limits["requests_per_day"], 100000)

    @patch("requests.get")
    def test_get_weather_data_success(self, mock_get):
        """Test successful weather data retrieval."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {"temperature_2m": [10.5] * 24 * 31},  # 31 days of hourly data
            "daily": {
                "temperature_2m_mean": [10.5] * 31,
                "temperature_2m_min": [5.0] * 31,
                "temperature_2m_max": [15.0] * 31,
            },
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        weather = self.provider.get_weather_data(37.8716, -122.2727, 2023, 1)

        # Verify result
        self.assertIsNotNone(weather)
        self.assertEqual(weather.year, 2023)
        self.assertEqual(weather.month, 1)
        self.assertAlmostEqual(weather.avg_temp_c, 10.5, places=1)
        self.assertEqual(weather.min_temp_c, 5.0)
        self.assertEqual(weather.max_temp_c, 15.0)
        self.assertEqual(weather.data_source, "OpenMeteo")

        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("latitude", call_args[1]["params"])
        self.assertIn("longitude", call_args[1]["params"])
        self.assertIn("start_date", call_args[1]["params"])
        self.assertIn("end_date", call_args[1]["params"])

    @patch("requests.get")
    def test_get_weather_data_api_error(self, mock_get):
        """Test handling of API errors."""
        # Mock API error
        mock_get.side_effect = Exception("API Error")

        weather = self.provider.get_weather_data(37.8716, -122.2727, 2023, 1)

        # Should return None on error
        self.assertIsNone(weather)

    @patch("requests.get")
    def test_get_daily_temperatures(self, mock_get):
        """Test getting daily temperatures."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"daily": {"temperature_2m_mean": [10, 12, 14, 16, 18]}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        temps = self.provider.get_daily_temperatures(
            37.8716, -122.2727, date(2023, 1, 1), date(2023, 1, 5)
        )

        # Verify result
        self.assertEqual(len(temps), 5)
        self.assertEqual(temps, [10, 12, 14, 16, 18])

    @patch("requests.get")
    def test_get_monthly_average(self, mock_get):
        """Test getting monthly average temperature."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {"temperature_2m": [10.5] * 24 * 31},
            "daily": {"temperature_2m_mean": [10.5] * 31},
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        avg_temp = self.provider.get_monthly_average(37.8716, -122.2727, 2023, 1)

        # Verify result
        self.assertIsNotNone(avg_temp)
        self.assertAlmostEqual(avg_temp, 10.5, places=1)


class TestNOAAProvider(unittest.TestCase):
    """Test NOAA weather provider (placeholder tests)."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = NOAAProvider()

    def test_provider_initialization(self):
        """Test NOAA provider initialization."""
        self.assertEqual(self.provider.base_url, "https://www.ncei.noaa.gov/data/")

    def test_validate_date_range(self):
        """Test date range validation for NOAA."""
        # Valid historical date range
        self.assertTrue(self.provider.validate_date_range(date(1950, 1, 1), date(2023, 12, 31)))

        # Too old
        self.assertFalse(self.provider.validate_date_range(date(1890, 1, 1), date(1890, 12, 31)))

        # Future date
        future_date = datetime.now().date().replace(year=datetime.now().year + 1)
        self.assertFalse(self.provider.validate_date_range(date(2023, 1, 1), future_date))

    def test_not_implemented_methods(self):
        """Test that NOAA methods are not yet implemented."""
        # All methods should return None or empty

        avg = self.provider.get_monthly_average(0, 0, 2023, 1)
        temps = self.provider.get_daily_temperatures(0, 0, date(2023, 1, 1), date(2023, 1, 31))
        weather = self.provider.get_weather_data(0, 0, 2023, 1)

        self.assertIsNone(avg)
        self.assertEqual(temps, [])
        self.assertIsNone(weather)

        # Station search
        station = self.provider.get_nearest_station(0, 0)
        self.assertIsNone(station)


if __name__ == "__main__":
    unittest.main()
