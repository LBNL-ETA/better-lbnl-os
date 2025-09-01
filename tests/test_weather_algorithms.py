"""Unit tests for weather algorithms."""

import unittest
import numpy as np
import math

from better_lbnl_os.core.weather.calculations import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    convert_temperature,
    convert_temperature_list,
    calculate_heating_degree_days,
    calculate_cooling_degree_days,
    calculate_monthly_average,
    estimate_monthly_hdd,
    estimate_monthly_cdd,
    validate_temperature_range
)


class TestTemperatureConversions(unittest.TestCase):
    """Test temperature conversion functions."""
    
    def test_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion."""
        self.assertAlmostEqual(celsius_to_fahrenheit(0), 32, places=2)
        self.assertAlmostEqual(celsius_to_fahrenheit(100), 212, places=2)
        self.assertAlmostEqual(celsius_to_fahrenheit(-40), -40, places=2)
        self.assertAlmostEqual(celsius_to_fahrenheit(20), 68, places=2)
        
    def test_fahrenheit_to_celsius(self):
        """Test Fahrenheit to Celsius conversion."""
        self.assertAlmostEqual(fahrenheit_to_celsius(32), 0, places=2)
        self.assertAlmostEqual(fahrenheit_to_celsius(212), 100, places=2)
        self.assertAlmostEqual(fahrenheit_to_celsius(-40), -40, places=2)
        self.assertAlmostEqual(fahrenheit_to_celsius(68), 20, places=2)
    
    def test_invalid_temperature_conversion(self):
        """Test conversion with invalid inputs."""
        self.assertTrue(math.isnan(celsius_to_fahrenheit(float('nan'))))
        self.assertTrue(math.isnan(fahrenheit_to_celsius(float('nan'))))
    
    def test_convert_temperature(self):
        """Test generic temperature conversion."""
        # Same unit
        self.assertEqual(convert_temperature(20, 'C', 'C'), 20)
        self.assertEqual(convert_temperature(68, 'F', 'F'), 68)
        
        # C to F
        self.assertAlmostEqual(convert_temperature(0, 'C', 'F'), 32, places=2)
        
        # F to C
        self.assertAlmostEqual(convert_temperature(32, 'F', 'C'), 0, places=2)
        
        # Invalid units
        with self.assertRaises(ValueError):
            convert_temperature(20, 'K', 'F')
    
    def test_convert_temperature_list(self):
        """Test list temperature conversion."""
        temps_c = [0, 20, 100]
        temps_f = convert_temperature_list(temps_c, 'C', 'F')
        
        self.assertAlmostEqual(temps_f[0], 32, places=2)
        self.assertAlmostEqual(temps_f[1], 68, places=2)
        self.assertAlmostEqual(temps_f[2], 212, places=2)
        
        # Empty list
        self.assertEqual(convert_temperature_list([], 'C', 'F'), [])


class TestDegreeDayCalculations(unittest.TestCase):
    """Test degree day calculation functions."""
    
    def test_heating_degree_days(self):
        """Test HDD calculation."""
        # All temps below base
        daily_temps = [30, 40, 50, 55, 60]
        hdd = calculate_heating_degree_days(daily_temps, base_temp=65.0)
        expected = (65-30) + (65-40) + (65-50) + (65-55) + (65-60)
        self.assertAlmostEqual(hdd, expected, places=2)
        
        # All temps above base
        daily_temps = [70, 75, 80]
        hdd = calculate_heating_degree_days(daily_temps, base_temp=65.0)
        self.assertEqual(hdd, 0)
        
        # Mixed temps
        daily_temps = [60, 65, 70]
        hdd = calculate_heating_degree_days(daily_temps, base_temp=65.0)
        self.assertAlmostEqual(hdd, 5.0, places=2)
    
    def test_cooling_degree_days(self):
        """Test CDD calculation."""
        # All temps above base
        daily_temps = [70, 75, 80, 85, 90]
        cdd = calculate_cooling_degree_days(daily_temps, base_temp=65.0)
        expected = (70-65) + (75-65) + (80-65) + (85-65) + (90-65)
        self.assertAlmostEqual(cdd, expected, places=2)
        
        # All temps below base
        daily_temps = [50, 55, 60]
        cdd = calculate_cooling_degree_days(daily_temps, base_temp=65.0)
        self.assertEqual(cdd, 0)
        
        # Mixed temps
        daily_temps = [60, 65, 70]
        cdd = calculate_cooling_degree_days(daily_temps, base_temp=65.0)
        self.assertAlmostEqual(cdd, 5.0, places=2)
    
    def test_degree_days_with_celsius(self):
        """Test degree days with Celsius inputs."""
        # Using Celsius base temperature (18.3°C ≈ 65°F)
        daily_temps_c = [10, 15, 20, 25]
        
        hdd = calculate_heating_degree_days(daily_temps_c, base_temp=18.3, temp_unit='C')
        expected_hdd = (18.3-10) + (18.3-15) + 0 + 0
        self.assertAlmostEqual(hdd, expected_hdd, places=1)
        
        cdd = calculate_cooling_degree_days(daily_temps_c, base_temp=18.3, temp_unit='C')
        expected_cdd = 0 + 0 + (20-18.3) + (25-18.3)
        self.assertAlmostEqual(cdd, expected_cdd, places=1)
    
    def test_degree_days_with_numpy_array(self):
        """Test degree days with numpy array input."""
        daily_temps = np.array([60, 65, 70, 75, 80])
        
        hdd = calculate_heating_degree_days(daily_temps, base_temp=65.0)
        self.assertAlmostEqual(hdd, 5.0, places=2)
        
        cdd = calculate_cooling_degree_days(daily_temps, base_temp=65.0)
        self.assertAlmostEqual(cdd, 20.0, places=2)


class TestMonthlyCalculations(unittest.TestCase):
    """Test monthly calculation functions."""
    
    def test_calculate_monthly_average(self):
        """Test monthly average calculation."""
        # Normal case
        hourly_temps = [20] * 24 * 30  # 30 days of constant 20°C
        avg = calculate_monthly_average(hourly_temps)
        self.assertAlmostEqual(avg, 20.0, places=2)
        
        # With variation
        hourly_temps = list(range(0, 24)) * 30  # 0-23 repeated
        avg = calculate_monthly_average(hourly_temps)
        self.assertAlmostEqual(avg, 11.5, places=2)
        
        # With NaN values
        hourly_temps = [20, float('nan'), 30, 40]
        avg = calculate_monthly_average(hourly_temps)
        self.assertAlmostEqual(avg, 30.0, places=2)  # (20+30+40)/3
        
        # Empty list
        self.assertTrue(math.isnan(calculate_monthly_average([])))
        
        # All NaN
        hourly_temps = [float('nan')] * 10
        self.assertTrue(math.isnan(calculate_monthly_average(hourly_temps)))
    
    def test_estimate_monthly_hdd(self):
        """Test monthly HDD estimation."""
        # Below base temp
        hdd = estimate_monthly_hdd(avg_temp=50, days_in_month=30, base_temp=65)
        self.assertAlmostEqual(hdd, (65-50)*30, places=2)
        
        # Above base temp
        hdd = estimate_monthly_hdd(avg_temp=70, days_in_month=30, base_temp=65)
        self.assertEqual(hdd, 0)
        
        # At base temp
        hdd = estimate_monthly_hdd(avg_temp=65, days_in_month=30, base_temp=65)
        self.assertEqual(hdd, 0)
        
        # With NaN
        hdd = estimate_monthly_hdd(avg_temp=float('nan'), days_in_month=30)
        self.assertEqual(hdd, 0)
    
    def test_estimate_monthly_cdd(self):
        """Test monthly CDD estimation."""
        # Above base temp
        cdd = estimate_monthly_cdd(avg_temp=75, days_in_month=30, base_temp=65)
        self.assertAlmostEqual(cdd, (75-65)*30, places=2)
        
        # Below base temp
        cdd = estimate_monthly_cdd(avg_temp=60, days_in_month=30, base_temp=65)
        self.assertEqual(cdd, 0)
        
        # At base temp
        cdd = estimate_monthly_cdd(avg_temp=65, days_in_month=30, base_temp=65)
        self.assertEqual(cdd, 0)
        
        # With NaN
        cdd = estimate_monthly_cdd(avg_temp=float('nan'), days_in_month=30)
        self.assertEqual(cdd, 0)


class TestTemperatureValidation(unittest.TestCase):
    """Test temperature validation functions."""
    
    def test_validate_temperature_range(self):
        """Test temperature range validation."""
        # Valid temperatures
        self.assertTrue(validate_temperature_range(20))
        self.assertTrue(validate_temperature_range(0))
        self.assertTrue(validate_temperature_range(-30))
        self.assertTrue(validate_temperature_range(50))
        self.assertTrue(validate_temperature_range(-59.9))
        self.assertTrue(validate_temperature_range(59.9))
        
        # Invalid temperatures
        self.assertFalse(validate_temperature_range(-100))
        self.assertFalse(validate_temperature_range(100))
        self.assertFalse(validate_temperature_range(float('nan')))
        self.assertFalse(validate_temperature_range(float('inf')))
        self.assertFalse(validate_temperature_range(float('-inf')))
    
    def test_validate_custom_range(self):
        """Test validation with custom range."""
        # Custom range
        self.assertTrue(validate_temperature_range(5, min_temp_c=0, max_temp_c=10))
        self.assertFalse(validate_temperature_range(-5, min_temp_c=0, max_temp_c=10))
        self.assertFalse(validate_temperature_range(15, min_temp_c=0, max_temp_c=10))


if __name__ == '__main__':
    unittest.main()
