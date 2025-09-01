"""Abstract interfaces for weather data providers."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional, Dict, Any

from better_lbnl_os.data.models import WeatherData, WeatherStation


class WeatherDataProvider(ABC):
    """Abstract interface for weather data providers."""
    
    @abstractmethod
    def get_monthly_average(
        self, 
        latitude: float, 
        longitude: float,
        year: int, 
        month: int
    ) -> Optional[float]:
        """
        Get monthly average temperature for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            year: Year (YYYY)
            month: Month (1-12)
            
        Returns:
            Monthly average temperature in Celsius, or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_daily_temperatures(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date
    ) -> List[float]:
        """
        Get daily temperatures for a date range.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date
            end_date: End date (inclusive)
            
        Returns:
            List of daily average temperatures in Celsius
        """
        pass
    
    @abstractmethod
    def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        year: int,
        month: int
    ) -> Optional[WeatherData]:
        """
        Get complete weather data for a month.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            year: Year (YYYY)
            month: Month (1-12)
            
        Returns:
            WeatherData object or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_nearest_station(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 100.0
    ) -> Optional[WeatherStation]:
        """
        Find the nearest weather station to a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            max_distance_km: Maximum search distance in kilometers
            
        Returns:
            WeatherStation object or None if no station within range
        """
        pass
    
    @abstractmethod
    def validate_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> bool:
        """
        Check if date range is valid for this provider.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            True if date range is valid
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the name of this weather data provider."""
        return self.__class__.__name__.replace('Provider', '')
    
    def get_api_limits(self) -> Dict[str, Any]:
        """
        Get API rate limits and restrictions.
        
        Returns:
            Dictionary with limit information
        """
        return {
            'requests_per_hour': None,
            'requests_per_day': None,
            'max_date_range_days': None,
            'historical_data_available': True
        }
