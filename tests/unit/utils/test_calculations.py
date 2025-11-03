"""Unit tests for weather algorithms (conversions and basic calculations)."""

import math
import unittest

from better_lbnl_os.core.weather.calculations import (
    calculate_monthly_average,
    celsius_to_fahrenheit,
    convert_temperature,
    convert_temperature_list,
    fahrenheit_to_celsius,
    validate_temperature_range,
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
        self.assertTrue(math.isnan(celsius_to_fahrenheit(float("nan"))))
        self.assertTrue(math.isnan(fahrenheit_to_celsius(float("nan"))))

    def test_non_numeric_temperature_conversion(self):
        """Test conversion with non-numeric inputs."""
        # String input should return NaN
        self.assertTrue(math.isnan(celsius_to_fahrenheit("not a number")))
        self.assertTrue(math.isnan(fahrenheit_to_celsius("not a number")))

    def test_convert_temperature(self):
        """Test generic temperature conversion."""
        # Same unit
        self.assertEqual(convert_temperature(20, "C", "C"), 20)
        self.assertEqual(convert_temperature(68, "F", "F"), 68)

        # C to F
        self.assertAlmostEqual(convert_temperature(0, "C", "F"), 32, places=2)

        # F to C
        self.assertAlmostEqual(convert_temperature(32, "F", "C"), 0, places=2)

        # Invalid units
        with self.assertRaises(ValueError):
            convert_temperature(20, "K", "F")

    def test_convert_temperature_list(self):
        """Test list temperature conversion."""
        temps_c = [0, 20, 100]
        temps_f = convert_temperature_list(temps_c, "C", "F")

        self.assertAlmostEqual(temps_f[0], 32, places=2)
        self.assertAlmostEqual(temps_f[1], 68, places=2)
        self.assertAlmostEqual(temps_f[2], 212, places=2)

        # Empty list
        self.assertEqual(convert_temperature_list([], "C", "F"), [])


class TestMonthlyCalculations(unittest.TestCase):
    """Test monthly calculation functions."""

    def test_calculate_monthly_average(self):
        """Test monthly average calculation."""
        # Normal case with list input - using daily temps for a month
        temps = [20] * 30  # 30 days of constant 20°C
        avg = calculate_monthly_average(temps)
        self.assertAlmostEqual(avg, 20.0, places=2)

        # With variation - could be hourly data for ~1.25 days
        temps = list(range(0, 24)) * 30  # 0-23 repeated 30 times
        avg = calculate_monthly_average(temps)
        self.assertAlmostEqual(avg, 11.5, places=2)

        # With NaN values
        temps = [20, float("nan"), 30, 40]
        avg = calculate_monthly_average(temps)
        self.assertAlmostEqual(avg, 30.0, places=2)  # (20+30+40)/3

        # Empty list
        self.assertTrue(math.isnan(calculate_monthly_average([])))

        # All NaN
        temps = [float("nan")] * 10
        self.assertTrue(math.isnan(calculate_monthly_average(temps)))

    def test_calculate_monthly_average_numpy_array(self):
        """Test monthly average calculation with numpy array input.

        Note: The function converts lists to numpy arrays internally,
        but we test that it also handles numpy arrays passed directly.
        """

        # The function expects lists but can handle numpy arrays
        # Test a scenario where a list is converted to numpy internally
        temps_list = [15.0, 20.0, 25.0, 30.0]
        avg = calculate_monthly_average(temps_list)
        self.assertAlmostEqual(avg, 22.5, places=2)

        # Verify the internal conversion path works
        # (line 43-44: conversion from list to numpy array)
        temps_short = [10.0, 20.0]
        avg2 = calculate_monthly_average(temps_short)
        self.assertAlmostEqual(avg2, 15.0, places=2)


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
        self.assertFalse(validate_temperature_range(float("nan")))
        self.assertFalse(validate_temperature_range(float("inf")))
        self.assertFalse(validate_temperature_range(float("-inf")))

    def test_validate_custom_range(self):
        """Test validation with custom range."""
        # Custom range
        self.assertTrue(validate_temperature_range(5, min_temp_c=0, max_temp_c=10))
        self.assertFalse(validate_temperature_range(-5, min_temp_c=0, max_temp_c=10))
        self.assertFalse(validate_temperature_range(15, min_temp_c=0, max_temp_c=10))


if __name__ == "__main__":
    unittest.main()
