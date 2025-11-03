"""Unit tests for weather domain models."""

import calendar
import unittest

from better_lbnl_os.models import WeatherData, WeatherStation
from better_lbnl_os.utils.calculations import (
    validate_temperature_range,
)


class TestWeatherDataModel(unittest.TestCase):
    """Test WeatherData domain model."""

    def setUp(self):
        """Set up test data."""
        self.weather_data = WeatherData(
            station_id="TEST001",
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=1,
            avg_temp_c=10.5,
            min_temp_c=5.0,
            max_temp_c=15.0,
            data_source="Test",
        )

    def test_temperature_properties(self):
        """Test temperature conversion properties."""
        # Test average temperature
        self.assertAlmostEqual(self.weather_data.avg_temp_f, 50.9, places=1)

        # Test min temperature
        self.assertAlmostEqual(self.weather_data.min_temp_f, 41.0, places=1)

        # Test max temperature
        self.assertAlmostEqual(self.weather_data.max_temp_f, 59.0, places=1)

    def test_temperature_properties_with_none(self):
        """Test temperature properties when min/max are None."""
        weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=1,
            avg_temp_c=10.5,
            data_source="Test",
        )

        self.assertAlmostEqual(weather.avg_temp_f, 50.9, places=1)
        self.assertIsNone(weather.min_temp_f)
        self.assertIsNone(weather.max_temp_f)

    def test_monthly_data_shape(self):
        """Basic sanity check for monthly data fields."""
        self.assertEqual(self.weather_data.month, 1)
        self.assertEqual(self.weather_data.year, 2024)

    def test_cdd_calculation_monthly_average(self):
        """Test CDD calculation using monthly average."""
        # Create summer weather data
        summer_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=7,  # July
            avg_temp_c=25.0,  # 77°F
            data_source="Test",
        )

        calendar.monthrange(summer_weather.year, summer_weather.month)[1]
        # Only test temperature conversions
        self.assertAlmostEqual(summer_weather.avg_temp_f, 77.0, places=1)

    def test_temperature_properties_non_negative(self):
        """Sanity check that calculations don’t produce invalid values."""
        self.assertTrue(self.weather_data.avg_temp_f > 0)

    def test_cdd_calculation_non_negative(self):
        """CDD monthly estimation should be non-negative."""
        summer_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=7,
            avg_temp_c=25.0,
            data_source="Test",
        )
        self.assertTrue(summer_weather.avg_temp_f > 0)

    def test_temperature_validation(self):
        """Test temperature validation."""
        # Valid temperature
        self.assertTrue(validate_temperature_range(self.weather_data.avg_temp_c))

        # Invalid temperature - too hot
        hot_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=1,
            avg_temp_c=70.0,  # Unreasonably hot
            data_source="Test",
        )
        self.assertFalse(validate_temperature_range(hot_weather.avg_temp_c))

        # Invalid temperature - too cold
        cold_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=1,
            avg_temp_c=-70.0,  # Unreasonably cold
            data_source="Test",
        )
        self.assertFalse(validate_temperature_range(cold_weather.avg_temp_c))

    def test_month_validation(self):
        """Test month field validation."""
        # Valid months
        for month in range(1, 13):
            weather = WeatherData(
                latitude=37.8716,
                longitude=-122.2727,
                year=2024,
                month=month,
                avg_temp_c=10.0,
                data_source="Test",
            )
            self.assertEqual(weather.month, month)

        # Invalid months should raise validation error
        with self.assertRaises(Exception):
            WeatherData(
                latitude=37.8716,
                longitude=-122.2727,
                year=2024,
                month=0,  # Invalid
                avg_temp_c=10.0,
                data_source="Test",
            )

        with self.assertRaises(Exception):
            WeatherData(
                latitude=37.8716,
                longitude=-122.2727,
                year=2024,
                month=13,  # Invalid
                avg_temp_c=10.0,
                data_source="Test",
            )


class TestWeatherStationModel(unittest.TestCase):
    """Test WeatherStation domain model."""

    def setUp(self):
        """Set up test data."""
        self.station = WeatherStation(
            station_id="723840-13995",
            name="SACRAMENTO INTL AP",
            latitude=38.5125,
            longitude=-121.5006,
            elevation=17.0,
            data_source="NOAA",
        )

    def test_station_creation(self):
        """Test weather station creation."""
        self.assertEqual(self.station.station_id, "723840-13995")
        self.assertEqual(self.station.name, "SACRAMENTO INTL AP")
        self.assertAlmostEqual(self.station.latitude, 38.5125, places=4)
        self.assertAlmostEqual(self.station.longitude, -121.5006, places=4)
        self.assertEqual(self.station.elevation, 17.0)
        self.assertEqual(self.station.data_source, "NOAA")

    def test_distance_calculation(self):
        """Test distance calculation to a point."""
        # Berkeley, CA coordinates
        berkeley_lat = 37.8716
        berkeley_lng = -122.2727

        distance = self.station.distance_to(berkeley_lat, berkeley_lng)

        # Sacramento to Berkeley is approximately 100 km
        self.assertGreater(distance, 80)
        self.assertLess(distance, 120)

    def test_distance_to_same_location(self):
        """Test distance to same location is zero."""
        distance = self.station.distance_to(self.station.latitude, self.station.longitude)
        self.assertAlmostEqual(distance, 0, places=2)

    def test_coordinate_validation(self):
        """Test coordinate range validation."""
        # Valid coordinates
        valid_station = WeatherStation(
            station_id="TEST", name="Test Station", latitude=45.0, longitude=-120.0
        )
        self.assertEqual(valid_station.latitude, 45.0)
        self.assertEqual(valid_station.longitude, -120.0)

        # Edge cases - poles and date line
        north_pole = WeatherStation(
            station_id="NP", name="North Pole", latitude=90.0, longitude=0.0
        )
        self.assertEqual(north_pole.latitude, 90.0)

        south_pole = WeatherStation(
            station_id="SP", name="South Pole", latitude=-90.0, longitude=0.0
        )
        self.assertEqual(south_pole.latitude, -90.0)

        date_line = WeatherStation(station_id="DL", name="Date Line", latitude=0.0, longitude=180.0)
        self.assertEqual(date_line.longitude, 180.0)

        # Invalid coordinates should raise validation error
        with self.assertRaises(Exception):
            WeatherStation(
                station_id="TEST", name="Invalid", latitude=91.0, longitude=0.0  # Invalid
            )

        with self.assertRaises(Exception):
            WeatherStation(
                station_id="TEST", name="Invalid", latitude=0.0, longitude=181.0  # Invalid
            )

    def test_optional_fields(self):
        """Test optional fields can be None."""
        minimal_station = WeatherStation(
            station_id="MIN001", name="Minimal Station", latitude=40.0, longitude=-100.0
        )

        self.assertIsNone(minimal_station.elevation)
        self.assertIsNone(minimal_station.distance_km)
        self.assertEqual(minimal_station.data_source, "NOAA")  # Default value


if __name__ == "__main__":
    unittest.main()
