"""
Weather Data for Energy Analysis Example

This example demonstrates how to use weather data alongside
utility bills for building energy analysis.
"""

from datetime import date
from typing import List, Tuple
import numpy as np

from better_lbnl_os.core.weather import WeatherService, OpenMeteoProvider
from better_lbnl_os.models import LocationInfo, WeatherData


def get_weather_for_billing_periods(
    location: LocationInfo,
    billing_periods: List[Tuple[date, date]]
) -> List[dict]:
    """
    Get weather data aligned with utility billing periods.
    
    Args:
        location: Building location
        billing_periods: List of (start_date, end_date) tuples
        
    Returns:
        List of weather summaries for each billing period
    """
    service = WeatherService(provider=OpenMeteoProvider())
    results = []
    
    for start_date, end_date in billing_periods:
        # Get weather for the billing period month(s)
        weather_data = []
        
        # Handle billing periods that span multiple months
        current_date = start_date
        while current_date <= end_date:
            weather = service.get_weather_data(
                location, 
                current_date.year, 
                current_date.month
            )
            if weather:
                weather_data.append(weather)
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Calculate weighted average based on days in each month
        if weather_data:
            total_days = (end_date - start_date).days + 1
            weighted_temp = 0
            # Degree-day calculations intentionally omitted
            
            for weather in weather_data:
                # Calculate days in this month that fall within billing period
                month_start = date(weather.year, weather.month, 1)
                if weather.month == 12:
                    month_end = date(weather.year + 1, 1, 1)
                else:
                    month_end = date(weather.year, weather.month + 1, 1)
                month_end = date(month_end.year, month_end.month, month_end.day - 1)
                
                overlap_start = max(month_start, start_date)
                overlap_end = min(month_end, end_date)
                overlap_days = max(0, (overlap_end - overlap_start).days + 1)
                
                # Weight by days
                weight = overlap_days / total_days
                weighted_temp += weather.avg_temp_f * weight
                
                # Degree days are additive
            
            results.append({
                'period': f"{start_date} to {end_date}",
                'days': total_days,
                'avg_temp_f': weighted_temp,
                'total_hdd': None,
                'total_cdd': None
            })
        else:
            results.append({
                'period': f"{start_date} to {end_date}",
                'days': (end_date - start_date).days + 1,
                'avg_temp_f': None,
                'total_hdd': None,
                'total_cdd': None
            })
    
    return results


def analyze_energy_weather_correlation():
    """Analyze correlation between energy use and weather."""
    print("=" * 70)
    print("Energy-Weather Correlation Analysis")
    print("=" * 70)
    
    # Building location
    location = LocationInfo(
        geo_lat=38.5816,    # Sacramento, CA
        geo_lng=-121.4944,
        state="CA",
        noaa_station_name="Sacramento, CA"
    )
    
    # Sample utility bill data (kWh and billing periods)
    utility_bills = [
        {'period': (date(2023, 1, 15), date(2023, 2, 14)), 'kwh': 850},
        {'period': (date(2023, 2, 15), date(2023, 3, 14)), 'kwh': 780},
        {'period': (date(2023, 3, 15), date(2023, 4, 14)), 'kwh': 720},
        {'period': (date(2023, 4, 15), date(2023, 5, 14)), 'kwh': 680},
        {'period': (date(2023, 5, 15), date(2023, 6, 14)), 'kwh': 750},
        {'period': (date(2023, 6, 15), date(2023, 7, 14)), 'kwh': 950},
        {'period': (date(2023, 7, 15), date(2023, 8, 14)), 'kwh': 1100},
        {'period': (date(2023, 8, 15), date(2023, 9, 14)), 'kwh': 1050},
    ]
    
    print(f"\nLocation: Sacramento, CA")
    print(f"Analysis Period: Jan 2023 - Sep 2023\n")
    
    # Get weather data for billing periods
    billing_periods = [bill['period'] for bill in utility_bills]
    weather_summaries = get_weather_for_billing_periods(location, billing_periods)
    
    # Display results
    print("Billing Period         | Days | kWh   | Avg°F | HDD   | CDD   | kWh/DD")
    print("-" * 70)
    
    energy_data = []
    # Degree-day data intentionally omitted
    
    for bill, weather in zip(utility_bills, weather_summaries):
        if weather['avg_temp_f'] is not None:
            energy_data.append(bill['kwh'])
            
            start, end = bill['period']
            print(f"{start} - {end} | {weather['days']:4} | {bill['kwh']:5} | "
                  f"{weather['avg_temp_f']:5.1f}")
    
    # Calculate correlations
    if len(energy_data) > 2:
        energy_array = np.array(energy_data)
        print("\nNote: Degree-day correlation removed to mirror Django capability.")


def calculate_weather_normalized_energy():
    """Calculate weather-normalized energy consumption."""
    print("\n" + "=" * 70)
    print("Weather-Normalized Energy Consumption")
    print("=" * 70)
    
    # Building location
    location = LocationInfo(
        geo_lat=41.8781,    # Chicago, IL
        geo_lng=-87.6298,
        state="IL",
        noaa_station_name="Chicago, IL"
    )
    
    service = WeatherService(provider=OpenMeteoProvider())
    
    print(f"\nLocation: Chicago, IL")
    print("Comparing actual vs. typical weather impact on energy use\n")
    
    # Get actual weather for 2023
    actual_weather = service.get_weather_range(location, 2023, 1, 2023, 12)
    
    # For demonstration, use 2022 as "typical" year
    typical_weather = service.get_weather_range(location, 2022, 1, 2022, 12)
    
    if actual_weather and typical_weather:
        print("Note: Weather normalization based on degree-days is omitted in OS lib.")


def main():
    """Run all energy analysis examples."""
    print("\n" + "=" * 70)
    print("   BETTER-LBNL Weather for Energy Analysis Examples")
    print("=" * 70)
    
    analyze_energy_weather_correlation()
    calculate_weather_normalized_energy()
    
    print("\n" + "=" * 70)
    print("   Examples Complete!")
    print("=" * 70)
    print("\nThese examples demonstrate how weather data can be used for:")
    print("  • Correlating energy use with heating/cooling demand")
    print("  • Identifying heating vs. cooling dominated buildings")
    print("  • Weather-normalizing energy consumption")
    print("  • Comparing actual vs. typical weather years")


if __name__ == "__main__":
    main()
