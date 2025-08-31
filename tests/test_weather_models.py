"""Unit tests for weather domain models."""

import unittest
from datetime import date
import calendar

from better_lbnl.data.models import WeatherData, WeatherStation


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
            data_source="Test"
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
            data_source="Test"
        )
        
        self.assertAlmostEqual(weather.avg_temp_f, 50.9, places=1)
        self.assertIsNone(weather.min_temp_f)
        self.assertIsNone(weather.max_temp_f)
    
    def test_hdd_calculation_monthly_average(self):
        """Test HDD calculation using monthly average."""
        # Without daily data, should use monthly estimation
        hdd = self.weather_data.calculate_hdd(base_temp_f=65.0, use_daily=False)
        
        # January has 31 days
        # avg_temp_f = 50.9, base = 65
        # HDD = (65 - 50.9) * 31
        expected_hdd = (65 - 50.9) * 31
        self.assertAlmostEqual(hdd, expected_hdd, places=1)
    
    def test_cdd_calculation_monthly_average(self):
        """Test CDD calculation using monthly average."""
        # Create summer weather data
        summer_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=7,  # July
            avg_temp_c=25.0,  # 77°F
            data_source="Test"
        )
        
        cdd = summer_weather.calculate_cdd(base_temp_f=65.0, use_daily=False)
        
        # July has 31 days
        # avg_temp_f = 77, base = 65
        # CDD = (77 - 65) * 31
        expected_cdd = (77 - 65) * 31
        self.assertAlmostEqual(cdd, expected_cdd, places=1)
    
    def test_hdd_calculation_with_daily_temps(self):
        """Test HDD calculation with daily temperature data."""
        # Create weather with daily temps
        daily_temps_c = [8, 10, 12, 9, 11, 7, 6] * 4 + [10, 11, 12]  # 31 days for January
        weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=1,
            avg_temp_c=10.5,
            data_source="Test",
            daily_temps_c=daily_temps_c
        )
        
        hdd = weather.calculate_hdd(base_temp_f=65.0, use_daily=True)
        
        # HDD should be calculated from daily temps
        # All temps are below 65°F (18.3°C), so all contribute to HDD
        self.assertGreater(hdd, 0)
        
        # Compare with monthly estimate
        hdd_monthly = weather.calculate_hdd(base_temp_f=65.0, use_daily=False)
        # Daily calculation should be different from monthly estimate
        self.assertNotAlmostEqual(hdd, hdd_monthly, places=0)
    
    def test_cdd_calculation_with_daily_temps(self):
        """Test CDD calculation with daily temperature data."""
        # Create summer weather with daily temps
        daily_temps_c = [20, 22, 24, 26, 28, 30, 25] * 4 + [25, 26, 27]  # 31 days
        weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=7,
            avg_temp_c=25.0,
            data_source="Test",
            daily_temps_c=daily_temps_c
        )
        
        cdd = weather.calculate_cdd(base_temp_f=65.0, use_daily=True)
        
        # Most temps are above 65°F (18.3°C), so they contribute to CDD
        self.assertGreater(cdd, 0)
        
        # Compare with monthly estimate
        cdd_monthly = weather.calculate_cdd(base_temp_f=65.0, use_daily=False)
        # Daily calculation should be different from monthly estimate
        self.assertNotAlmostEqual(cdd, cdd_monthly, places=0)
    
    def test_temperature_validation(self):
        """Test temperature validation."""
        # Valid temperature
        self.assertTrue(self.weather_data.is_valid_temperature())
        
        # Invalid temperature - too hot
        hot_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=1,
            avg_temp_c=70.0,  # Unreasonably hot
            data_source="Test"
        )
        self.assertFalse(hot_weather.is_valid_temperature())
        
        # Invalid temperature - too cold
        cold_weather = WeatherData(
            latitude=37.8716,
            longitude=-122.2727,
            year=2024,
            month=1,
            avg_temp_c=-70.0,  # Unreasonably cold
            data_source="Test"
        )
        self.assertFalse(cold_weather.is_valid_temperature())
    
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
                data_source="Test"
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
                data_source="Test"
            )
        
        with self.assertRaises(Exception):
            WeatherData(
                latitude=37.8716,
                longitude=-122.2727,
                year=2024,
                month=13,  # Invalid
                avg_temp_c=10.0,
                data_source="Test"
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
            data_source="NOAA"
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
        distance = self.station.distance_to(
            self.station.latitude,
            self.station.longitude
        )
        self.assertAlmostEqual(distance, 0, places=2)
    
    def test_coordinate_validation(self):
        """Test coordinate range validation."""
        # Valid coordinates
        valid_station = WeatherStation(
            station_id="TEST",
            name="Test Station",
            latitude=45.0,
            longitude=-120.0
        )
        self.assertEqual(valid_station.latitude, 45.0)
        self.assertEqual(valid_station.longitude, -120.0)
        
        # Edge cases - poles and date line
        north_pole = WeatherStation(
            station_id="NP",
            name="North Pole",
            latitude=90.0,
            longitude=0.0
        )
        self.assertEqual(north_pole.latitude, 90.0)
        
        south_pole = WeatherStation(
            station_id="SP",
            name="South Pole",
            latitude=-90.0,
            longitude=0.0
        )
        self.assertEqual(south_pole.latitude, -90.0)
        
        date_line = WeatherStation(
            station_id="DL",
            name="Date Line",
            latitude=0.0,
            longitude=180.0
        )
        self.assertEqual(date_line.longitude, 180.0)
        
        # Invalid coordinates should raise validation error
        with self.assertRaises(Exception):
            WeatherStation(
                station_id="TEST",
                name="Invalid",
                latitude=91.0,  # Invalid
                longitude=0.0
            )
        
        with self.assertRaises(Exception):
            WeatherStation(
                station_id="TEST",
                name="Invalid",
                latitude=0.0,
                longitude=181.0  # Invalid
            )
    
    def test_optional_fields(self):
        """Test optional fields can be None."""
        minimal_station = WeatherStation(
            station_id="MIN001",
            name="Minimal Station",
            latitude=40.0,
            longitude=-100.0
        )
        
        self.assertIsNone(minimal_station.elevation)
        self.assertIsNone(minimal_station.distance_km)
        self.assertEqual(minimal_station.data_source, "NOAA")  # Default value


if __name__ == '__main__':
    unittest.main()