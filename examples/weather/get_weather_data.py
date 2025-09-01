"""
Example: Getting Weather Data using OpenMeteo Provider

This example demonstrates how to retrieve weather data for a location
using the BETTER-LBNL weather module.
"""

from datetime import date
from better_lbnl_os.core.weather import WeatherService, OpenMeteoProvider
from better_lbnl_os.data.models import LocationInfo


def get_monthly_weather():
    """Get weather data for a single month."""
    print("=" * 60)
    print("EXAMPLE 1: Get Weather for a Single Month")
    print("=" * 60)
    
    # Define location (Berkeley, CA)
    location = LocationInfo(
        geo_lat=37.8716,
        geo_lng=-122.2727,
        zipcode="94709",
        state="CA",
        country_code="US",
        noaa_station_name="Berkeley, CA"
    )
    
    # Create weather service with OpenMeteo provider
    service = WeatherService(provider=OpenMeteoProvider())
    
    # Get weather for January 2023
    weather = service.get_weather_data(location, 2023, 1)
    
    if weather:
        print(f"\nLocation: Berkeley, CA ({location.geo_lat}, {location.geo_lng})")
        print(f"Period: January 2023")
        print(f"Average Temperature: {weather.avg_temp_c:.1f}°C / {weather.avg_temp_f:.1f}°F")
        
        if weather.min_temp_c and weather.max_temp_c:
            print(f"Temperature Range: {weather.min_temp_c:.1f}°C to {weather.max_temp_c:.1f}°C")
        
        # Calculate degree days
        hdd = weather.calculate_hdd(base_temp_f=65.0)
        cdd = weather.calculate_cdd(base_temp_f=65.0)
        print(f"Heating Degree Days (HDD): {hdd:.1f}")
        print(f"Cooling Degree Days (CDD): {cdd:.1f}")
    else:
        print("Failed to retrieve weather data")


def get_annual_weather():
    """Get weather data for an entire year."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Get Weather for an Entire Year")
    print("=" * 60)
    
    # Define location (Phoenix, AZ - hot climate example)
    location = LocationInfo(
        geo_lat=33.4484,
        geo_lng=-112.0740,
        zipcode="85001",
        state="AZ",
        country_code="US",
        noaa_station_name="Phoenix, AZ"
    )
    
    # Create weather service
    service = WeatherService(provider=OpenMeteoProvider())
    
    # Get weather for all of 2023
    print(f"\nLocation: Phoenix, AZ ({location.geo_lat}, {location.geo_lng})")
    print("Fetching weather data for 2023...")
    
    weather_data = WeatherService(provider=OpenMeteoProvider()).get_weather_range(
        location, 2023, 1, 2023, 12
    )
    
    if weather_data:
        print(f"Retrieved {len(weather_data)} months of data\n")
        
        # Display monthly summary
        print("Month  | Avg Temp (°C) | Avg Temp (°F) | HDD    | CDD")
        print("-" * 56)
        
        total_hdd = 0
        total_cdd = 0
        
        for weather in weather_data:
            hdd = weather.calculate_hdd(base_temp_f=65.0)
            cdd = weather.calculate_cdd(base_temp_f=65.0)
            total_hdd += hdd
            total_cdd += cdd
            
            month_name = date(weather.year, weather.month, 1).strftime('%b')
            print(f"{month_name:6} | {weather.avg_temp_c:13.1f} | {weather.avg_temp_f:13.1f} | "
                  f"{hdd:6.1f} | {cdd:6.1f}")
        
        print("-" * 56)
        print(f"TOTAL  | {' ' * 13} | {' ' * 13} | {total_hdd:6.1f} | {total_cdd:6.1f}")
        
        # Annual summary
        print(f"\n2023 Annual Summary:")
        print(f"  Total Heating Degree Days: {total_hdd:.0f}")
        print(f"  Total Cooling Degree Days: {total_cdd:.0f}")
        print(f"  Climate: {'Cooling-dominated' if total_cdd > total_hdd else 'Heating-dominated'}")
    else:
        print("Failed to retrieve weather data")


def compare_locations():
    """Compare weather between multiple locations."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Compare Weather Across Locations")
    print("=" * 60)
    
    # Define multiple locations
    locations = [
        {
            "name": "San Francisco, CA",
            "location": LocationInfo(geo_lat=37.7749, geo_lng=-122.4194, state="CA")
        },
        {
            "name": "Chicago, IL",
            "location": LocationInfo(geo_lat=41.8781, geo_lng=-87.6298, state="IL")
        },
        {
            "name": "Miami, FL",
            "location": LocationInfo(geo_lat=25.7617, geo_lng=-80.1918, state="FL")
        },
        {
            "name": "Denver, CO",
            "location": LocationInfo(geo_lat=39.7392, geo_lng=-104.9903, state="CO")
        }
    ]
    
    # Create weather service
    service = WeatherService(provider=OpenMeteoProvider())
    
    # Compare July 2023 weather
    print("\nComparing July 2023 Weather:\n")
    print("Location         | Avg Temp (°F) | HDD  | CDD  | Climate Type")
    print("-" * 65)
    
    for loc_info in locations:
        weather = service.get_weather_data(loc_info["location"], 2023, 7)
        
        if weather:
            hdd = weather.calculate_hdd(base_temp_f=65.0)
            cdd = weather.calculate_cdd(base_temp_f=65.0)
            
            # Determine climate type based on degree days
            if cdd > 200:
                climate = "Hot Summer"
            elif cdd > 100:
                climate = "Warm Summer"
            elif hdd > 50:
                climate = "Cool Summer"
            else:
                climate = "Mild Summer"
            
            print(f"{loc_info['name']:16} | {weather.avg_temp_f:13.1f} | "
                  f"{hdd:4.0f} | {cdd:4.0f} | {climate}")


def find_weather_station():
    """Find the nearest weather station for a location."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Find Weather Station")
    print("=" * 60)
    
    # Create weather service
    service = WeatherService(provider=OpenMeteoProvider())
    
    # Find station for a location
    lat, lng = 40.7128, -74.0060  # New York City
    
    station = service.find_nearest_station(lat, lng)
    
    if station:
        print(f"\nLocation: New York City ({lat}, {lng})")
        print(f"Nearest Station: {station.name}")
        print(f"Station ID: {station.station_id}")
        print(f"Station Location: ({station.latitude}, {station.longitude})")
        print(f"Distance: {station.distance_km:.1f} km")
        print(f"Data Source: {station.data_source}")
        
        # Note about OpenMeteo
        print("\nNote: OpenMeteo uses gridded data rather than physical weather stations,")
        print("so it provides data for any location globally.")


def calculate_degree_days_with_custom_base():
    """Calculate degree days with custom base temperatures."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Custom Base Temperature Degree Days")
    print("=" * 60)
    
    # Location
    location = LocationInfo(
        geo_lat=34.0522,
        geo_lng=-118.2437,
        state="CA",
        noaa_station_name="Los Angeles, CA"
    )
    
    # Create weather service
    service = WeatherService(provider=OpenMeteoProvider())
    
    # Get weather for June 2023
    weather = service.get_weather_data(location, 2023, 6)
    
    if weather:
        print(f"\nLocation: Los Angeles, CA")
        print(f"Period: June 2023")
        print(f"Average Temperature: {weather.avg_temp_f:.1f}°F\n")
        
        # Calculate degree days with different base temperatures
        print("Base Temp | HDD    | CDD")
        print("-" * 25)
        
        for base_temp in [60, 65, 70, 75]:
            hdd = weather.calculate_hdd(base_temp_f=base_temp)
            cdd = weather.calculate_cdd(base_temp_f=base_temp)
            print(f"{base_temp:>9}°F | {hdd:6.1f} | {cdd:6.1f}")
        
        print("\nNote: Different base temperatures are used for different applications:")
        print("  - 65°F: Common residential standard")
        print("  - 60°F: Often used for commercial buildings")
        print("  - 70°F: May be used for cooling-dominated climates")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("   BETTER-LBNL Weather Data Examples")
    print("   Using OpenMeteo Weather Provider")
    print("=" * 60)
    
    # Get provider info
    service = WeatherService(provider=OpenMeteoProvider())
    info = service.get_provider_info()
    print(f"\nProvider: {info['name']}")
    print(f"API Limits: {info['limits']['requests_per_day']} requests/day")
    print(f"Historical data available from: {info['limits'].get('data_from_year', 'Unknown')}")
    
    # Run examples
    get_monthly_weather()
    get_annual_weather()
    compare_locations()
    find_weather_station()
    calculate_degree_days_with_custom_base()
    
    print("\n" + "=" * 60)
    print("   Examples Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
