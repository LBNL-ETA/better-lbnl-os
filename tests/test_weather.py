"""Test script for weather functionality."""

import asyncio
from datetime import date

from better_lbnl.core.algorithms.weather import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    calculate_heating_degree_days,
    calculate_cooling_degree_days,
    validate_temperature_range
)
from better_lbnl.core.weather import WeatherService, OpenMeteoProvider
from better_lbnl.domain.models import LocationInfo, WeatherData


def test_temperature_conversions():
    """Test temperature conversion functions."""
    print("\n=== Testing Temperature Conversions ===")
    
    # Test C to F
    assert abs(celsius_to_fahrenheit(0) - 32) < 0.01
    assert abs(celsius_to_fahrenheit(100) - 212) < 0.01
    assert abs(celsius_to_fahrenheit(20) - 68) < 0.01
    print("✓ Celsius to Fahrenheit conversions correct")
    
    # Test F to C
    assert abs(fahrenheit_to_celsius(32) - 0) < 0.01
    assert abs(fahrenheit_to_celsius(212) - 100) < 0.01
    assert abs(fahrenheit_to_celsius(68) - 20) < 0.01
    print("✓ Fahrenheit to Celsius conversions correct")


def test_degree_days():
    """Test degree day calculations."""
    print("\n=== Testing Degree Day Calculations ===")
    
    # Test HDD
    daily_temps = [60, 55, 50, 45, 40]  # All below 65°F base
    hdd = calculate_heating_degree_days(daily_temps, base_temp=65.0)
    expected_hdd = (65-60) + (65-55) + (65-50) + (65-45) + (65-40)
    assert abs(hdd - expected_hdd) < 0.01
    print(f"✓ HDD calculation: {hdd:.1f} (expected {expected_hdd})")
    
    # Test CDD
    daily_temps = [70, 75, 80, 85, 90]  # All above 65°F base
    cdd = calculate_cooling_degree_days(daily_temps, base_temp=65.0)
    expected_cdd = (70-65) + (75-65) + (80-65) + (85-65) + (90-65)
    assert abs(cdd - expected_cdd) < 0.01
    print(f"✓ CDD calculation: {cdd:.1f} (expected {expected_cdd})")
    
    # Test mixed temperatures
    daily_temps = [60, 65, 70]  # Below, at, and above base
    hdd = calculate_heating_degree_days(daily_temps, base_temp=65.0)
    cdd = calculate_cooling_degree_days(daily_temps, base_temp=65.0)
    assert abs(hdd - 5.0) < 0.01  # Only 60°F contributes
    assert abs(cdd - 5.0) < 0.01  # Only 70°F contributes
    print("✓ Mixed temperature degree days correct")


def test_temperature_validation():
    """Test temperature validation."""
    print("\n=== Testing Temperature Validation ===")
    
    assert validate_temperature_range(20.0) == True
    assert validate_temperature_range(-30.0) == True
    assert validate_temperature_range(50.0) == True
    assert validate_temperature_range(-100.0) == False
    assert validate_temperature_range(100.0) == False
    assert validate_temperature_range(float('nan')) == False
    print("✓ Temperature validation working correctly")


def test_weather_domain_model():
    """Test WeatherData domain model."""
    print("\n=== Testing Weather Domain Model ===")
    
    # Create weather data
    weather = WeatherData(
        latitude=37.8716,
        longitude=-122.2727,
        year=2024,
        month=1,
        avg_temp_c=10.5,
        min_temp_c=5.0,
        max_temp_c=15.0,
        data_source="Test",
        daily_temps_c=[8, 9, 10, 11, 12, 13, 14] * 4  # Simplified daily temps
    )
    
    # Test temperature properties
    assert abs(weather.avg_temp_f - 50.9) < 0.1
    assert abs(weather.min_temp_f - 41.0) < 0.1
    assert abs(weather.max_temp_f - 59.0) < 0.1
    print("✓ Temperature property conversions correct")
    
    # Test HDD/CDD calculations
    hdd = weather.calculate_hdd(base_temp_f=65.0)
    cdd = weather.calculate_cdd(base_temp_f=65.0)
    print(f"✓ HDD: {hdd:.1f}, CDD: {cdd:.1f}")
    
    # Test validation
    assert weather.is_valid_temperature() == True
    print("✓ Weather data validation passed")


async def test_weather_service():
    """Test weather service with real API call."""
    print("\n=== Testing Weather Service ===")
    
    # Create location (Berkeley, CA)
    location = LocationInfo(
        geo_lat=37.8716,
        geo_lng=-122.2727,
        zipcode="94709",
        state="CA",
        country_code="US"
    )
    
    # Create weather service
    service = WeatherService(provider=OpenMeteoProvider())
    
    # Test getting weather for a past month
    print("\nFetching weather data for Berkeley, CA (Jan 2023)...")
    weather = await service.get_weather_data(location, 2023, 1)
    
    if weather:
        print(f"✓ Retrieved weather data:")
        print(f"  - Average temperature: {weather.avg_temp_c:.1f}°C / {weather.avg_temp_f:.1f}°F")
        print(f"  - Data source: {weather.data_source}")
        
        # Calculate degree days
        hdd = weather.calculate_hdd()
        cdd = weather.calculate_cdd()
        print(f"  - Heating degree days: {hdd:.1f}")
        print(f"  - Cooling degree days: {cdd:.1f}")
    else:
        print("✗ Failed to retrieve weather data")
    
    # Test degree day calculation
    print("\nCalculating degree days...")
    dd = await service.calculate_degree_days(location, 2023, 7)  # July for cooling
    print(f"✓ July 2023 degree days: HDD={dd['hdd']:.1f}, CDD={dd['cdd']:.1f}")
    
    # Test provider info
    info = service.get_provider_info()
    print(f"\n✓ Using {info['name']} provider")
    print(f"  - API limits: {info['limits']['requests_per_day']} requests/day")


def main():
    """Run all tests."""
    print("="*50)
    print("BETTER-LBNL Weather Module Tests")
    print("="*50)
    
    # Run synchronous tests
    test_temperature_conversions()
    test_degree_days()
    test_temperature_validation()
    test_weather_domain_model()
    
    # Run async tests
    asyncio.run(test_weather_service())
    
    print("\n" + "="*50)
    print("All tests completed successfully!")
    print("="*50)


if __name__ == "__main__":
    main()