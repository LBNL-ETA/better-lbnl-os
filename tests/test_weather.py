"""Test script for weather functionality."""

from datetime import date

from better_lbnl_os.core.weather.calculations import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    convert_temperature,
    convert_temperature_list,
    calculate_monthly_average,
    validate_temperature_range,
)
from better_lbnl_os.core.weather import WeatherService, OpenMeteoProvider
from better_lbnl_os.models import LocationInfo, WeatherData
import calendar


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


def test_temperature_lists_and_average():
    """Test list conversions and monthly average."""
    temps_c = [0, 10, 20, 30]
    temps_f = convert_temperature_list(temps_c, 'C', 'F')
    assert temps_f == [32.0, 50.0, 68.0, 86.0]
    avg = calculate_monthly_average(temps_c)
    assert abs(avg - 15.0) < 0.01


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
    )
    
    # Test temperature properties
    assert abs(weather.avg_temp_f - 50.9) < 0.1
    assert abs(weather.min_temp_f - 41.0) < 0.1
    assert abs(weather.max_temp_f - 59.0) < 0.1
    print("✓ Temperature property conversions correct")
    
    # Test validation
    assert validate_temperature_range(weather.avg_temp_c) == True
    print("✓ Weather data validation passed")


def demo_weather_service():
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
    weather = service.get_weather_data(location, 2023, 1)
    
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
    
    # Run service demo (not executed by pytest)
    demo_weather_service()
    
    print("\n" + "="*50)
    print("All tests completed successfully!")
    print("="*50)


if __name__ == "__main__":
    main()
