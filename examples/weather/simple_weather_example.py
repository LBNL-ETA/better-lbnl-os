"""Simple Weather Data Example.

This is a minimal example showing how to get weather data
for a location.
"""

from better_lbnl_os.core.weather import OpenMeteoProvider, WeatherService
from better_lbnl_os.models import LocationInfo


def main():
    # 1. Define your location
    location = LocationInfo(
        geo_lat=37.8716,    # Berkeley, CA
        geo_lng=-122.2727,
        zipcode="94709",
        state="CA"
    )

    # 2. Create weather service
    service = WeatherService(provider=OpenMeteoProvider())

    # 3. Get weather data for January 2023
    weather = service.get_weather_data(location, 2023, 1)

    # 4. Display results
    if weather:
        print(f"Average Temperature: {weather.avg_temp_c:.1f}°C / {weather.avg_temp_f:.1f}°F")
    else:
        print("Failed to retrieve weather data")


if __name__ == "__main__":
    main()
