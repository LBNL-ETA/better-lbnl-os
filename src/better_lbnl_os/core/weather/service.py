"""High-level weather service for fetching and processing weather data."""

import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any

from better_lbnl_os.data.models import LocationInfo, WeatherData, WeatherStation
from better_lbnl_os.interfaces.weather_source import WeatherDataProvider
from .providers import OpenMeteoProvider


logger = logging.getLogger(__name__)


class WeatherService:
    """High-level weather service for fetching and processing weather data."""
    
    def __init__(self, provider: Optional[WeatherDataProvider] = None):
        """
        Initialize weather service.
        
        Args:
            provider: Weather data provider to use (defaults to OpenMeteo)
        """
        self.provider = provider or OpenMeteoProvider()
        logger.info(f"Weather service initialized with {self.provider.get_provider_name()} provider")
    
    def get_weather_data(
        self,
        location: LocationInfo,
        year: int,
        month: int
    ) -> Optional[WeatherData]:
        """
        Get weather data for a location and time period.
        
        Args:
            location: Location information
            year: Year (YYYY)
            month: Month (1-12)
            
        Returns:
            WeatherData object or None if unavailable
        """
        try:
            # Validate location
            if not location.is_valid_coordinates():
                logger.error(f"Invalid coordinates: {location.geo_lat}, {location.geo_lng}")
                return None
            
            # Get weather data from provider
            weather = self.provider.get_weather_data(
                location.geo_lat,
                location.geo_lng,
                year,
                month
            )
            
            if weather:
                # Add station info if available from location
                if location.noaa_station_id:
                    weather.station_id = location.noaa_station_id
                
                logger.info(f"Retrieved weather data for {year}-{month:02d}")
            else:
                logger.warning(f"No weather data available for {year}-{month:02d}")
            
            return weather
            
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            return None
    
    def get_weather_range(
        self,
        location: LocationInfo,
        start_year: int,
        start_month: int,
        end_year: int,
        end_month: int
    ) -> List[WeatherData]:
        """
        Get weather data for a date range.
        
        Args:
            location: Location information
            start_year: Start year
            start_month: Start month
            end_year: End year
            end_month: End month
            
        Returns:
            List of WeatherData objects
        """
        weather_data = []
        
        # Generate list of year-month pairs
        current_year = start_year
        current_month = start_month
        
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            weather = self.get_weather_data(location, current_year, current_month)
            if weather:
                weather_data.append(weather)
            
            # Move to next month
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        logger.info(f"Retrieved {len(weather_data)} months of weather data")
        return weather_data
    
    def fill_missing_weather(
        self,
        location: LocationInfo,
        start_year: int,
        start_month: int,
        end_year: int,
        end_month: int,
        existing_data: Optional[List[WeatherData]] = None
    ) -> List[WeatherData]:
        """
        Fill missing weather data for a date range.
        
        Args:
            location: Location information
            start_year: Start year
            start_month: Start month
            end_year: End year
            end_month: End month
            existing_data: Optional list of existing weather data
            
        Returns:
            List of WeatherData objects including filled gaps
        """
        # Create set of existing year-month pairs
        existing_periods = set()
        if existing_data:
            for weather in existing_data:
                existing_periods.add((weather.year, weather.month))
        
        filled_data = []
        
        # Generate list of year-month pairs
        current_year = start_year
        current_month = start_month
        
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            # Check if we already have data for this period
            if (current_year, current_month) not in existing_periods:
                # Fetch missing data
                weather = self.get_weather_data(location, current_year, current_month)
                if weather:
                    filled_data.append(weather)
                    logger.info(f"Filled missing weather data for {current_year}-{current_month:02d}")
            
            # Move to next month
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        # Combine with existing data if provided
        if existing_data:
            filled_data.extend(existing_data)
        
        # Sort by year and month
        filled_data.sort(key=lambda w: (w.year, w.month))
        
        logger.info(f"Filled {len(filled_data)} months of weather data")
        return filled_data
    
    def find_nearest_station(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 100.0
    ) -> Optional[WeatherStation]:
        """
        Find the nearest weather station.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            max_distance_km: Maximum search distance
            
        Returns:
            WeatherStation object or None
        """
        return self.provider.get_nearest_station(
            latitude,
            longitude,
            max_distance_km
        )
    
    def validate_data_availability(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> bool:
        """
        Check if weather data is available for date range.
        
        Args:
            start_date: Start date
            end_date: End date (defaults to today)
            
        Returns:
            True if data is available
        """
        if end_date is None:
            end_date = datetime.now().date()
        
        return self.provider.validate_date_range(start_date, end_date)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current weather provider.
        
        Returns:
            Dictionary with provider information
        """
        return {
            'name': self.provider.get_provider_name(),
            'limits': self.provider.get_api_limits()
        }
    
    def calculate_degree_days(
        self,
        location: LocationInfo,
        year: int,
        month: int,
        base_temp_f: float = 65.0
    ) -> Dict[str, float]:
        """
        Calculate heating and cooling degree days for a month.
        
        Args:
            location: Location information
            year: Year
            month: Month
            base_temp_f: Base temperature in Fahrenheit
            
        Returns:
            Dictionary with 'hdd' and 'cdd' values
        """
        weather = self.get_weather_data(location, year, month)
        
        if not weather:
            return {'hdd': 0.0, 'cdd': 0.0}
        
        hdd = weather.calculate_hdd(base_temp_f)
        cdd = weather.calculate_cdd(base_temp_f)
        
        return {'hdd': hdd, 'cdd': cdd}
    
    def calculate_annual_degree_days(
        self,
        location: LocationInfo,
        year: int,
        base_temp_f: float = 65.0
    ) -> Dict[str, float]:
        """
        Calculate annual heating and cooling degree days.
        
        Args:
            location: Location information
            year: Year
            base_temp_f: Base temperature in Fahrenheit
            
        Returns:
            Dictionary with 'hdd' and 'cdd' totals
        """
        total_hdd = 0.0
        total_cdd = 0.0
        
        # Get weather for all 12 months
        weather_data = self.get_weather_range(
            location, year, 1, year, 12
        )
        
        for weather in weather_data:
            total_hdd += weather.calculate_hdd(base_temp_f)
            total_cdd += weather.calculate_cdd(base_temp_f)
        
        logger.info(f"Annual degree days for {year}: HDD={total_hdd:.1f}, CDD={total_cdd:.1f}")
        
        return {
            'hdd': total_hdd,
            'cdd': total_cdd,
            'months_available': len(weather_data)
        }
