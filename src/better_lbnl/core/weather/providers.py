"""Weather data provider implementations."""

import logging
import math
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

import pandas as pd
import requests
from requests.exceptions import RequestException

from better_lbnl.core.algorithms.weather import calculate_monthly_average
from better_lbnl.domain.models import WeatherData, WeatherStation
from .interfaces import WeatherDataProvider


logger = logging.getLogger(__name__)


class OpenMeteoProvider(WeatherDataProvider):
    """OpenMeteo weather data provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenMeteo provider.
        
        Args:
            api_key: Optional API key for commercial tier
        """
        self.api_key = api_key
        if api_key:
            self.base_url = "https://customer-archive-api.open-meteo.com/v1/archive"
        else:
            self.base_url = "https://archive-api.open-meteo.com/v1/archive"
    
    async def get_monthly_average(
        self,
        latitude: float,
        longitude: float,
        year: int,
        month: int
    ) -> Optional[float]:
        """Get monthly average temperature from OpenMeteo."""
        try:
            # Get the weather data for the month
            weather_data = await self.get_weather_data(latitude, longitude, year, month)
            if weather_data:
                return weather_data.avg_temp_c
            return None
        except Exception as e:
            logger.error(f"Error getting monthly average from OpenMeteo: {e}")
            return None
    
    async def get_daily_temperatures(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date
    ) -> List[float]:
        """Get daily temperatures from OpenMeteo."""
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'daily': 'temperature_2m_mean',
                'timezone': 'UTC'
            }
            
            if self.api_key:
                params['apikey'] = self.api_key
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if 'daily' in data and 'temperature_2m_mean' in data['daily']:
                return data['daily']['temperature_2m_mean']
            
            return []
            
        except RequestException as e:
            logger.error(f"Error fetching daily temps from OpenMeteo: {e}")
            return []
    
    async def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        year: int,
        month: int
    ) -> Optional[WeatherData]:
        """Get complete weather data for a month from OpenMeteo."""
        try:
            # Validate inputs
            if not self.validate_date_range(
                date(year, month, 1),
                date(year, month, 1)
            ):
                logger.warning(f"Invalid date range for OpenMeteo: {year}-{month}")
                return None
            
            # Calculate date range for the month
            start_date = pd.Timestamp(year, month, 1)
            if month == 12:
                end_date = pd.Timestamp(year + 1, 1, 1) - pd.Timedelta(days=1)
            else:
                end_date = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)
            
            # Build request parameters
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'hourly': 'temperature_2m',
                'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean',
                'timezone': 'UTC'
            }
            
            if self.api_key:
                params['apikey'] = self.api_key
            
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract hourly temperatures
            hourly_temps = None
            if 'hourly' in data and 'temperature_2m' in data['hourly']:
                hourly_temps = data['hourly']['temperature_2m']
                avg_temp_c = calculate_monthly_average(hourly_temps)
            else:
                logger.warning("No hourly data in OpenMeteo response")
                return None
            
            # Extract daily temperatures if available
            daily_temps = None
            min_temp = None
            max_temp = None
            
            if 'daily' in data:
                daily_data = data['daily']
                if 'temperature_2m_mean' in daily_data:
                    daily_temps = daily_data['temperature_2m_mean']
                if 'temperature_2m_min' in daily_data:
                    min_temps = [t for t in daily_data['temperature_2m_min'] if t is not None]
                    min_temp = min(min_temps) if min_temps else None
                if 'temperature_2m_max' in daily_data:
                    max_temps = [t for t in daily_data['temperature_2m_max'] if t is not None]
                    max_temp = max(max_temps) if max_temps else None
            
            # Create WeatherData object
            weather = WeatherData(
                latitude=latitude,
                longitude=longitude,
                year=year,
                month=month,
                avg_temp_c=avg_temp_c,
                min_temp_c=min_temp,
                max_temp_c=max_temp,
                data_source="OpenMeteo",
                daily_temps_c=daily_temps
            )
            
            logger.debug(f"Retrieved weather data from OpenMeteo: {year}-{month}, avg: {avg_temp_c:.1f}°C")
            return weather
            
        except RequestException as e:
            logger.error(f"OpenMeteo API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing OpenMeteo data: {e}")
            return None
    
    def get_nearest_station(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 100.0
    ) -> Optional[WeatherStation]:
        """
        OpenMeteo uses gridded data, not stations.
        Returns a virtual station at the requested location.
        """
        return WeatherStation(
            station_id=f"GRID_{latitude:.2f}_{longitude:.2f}",
            name=f"OpenMeteo Grid Point ({latitude:.2f}, {longitude:.2f})",
            latitude=latitude,
            longitude=longitude,
            elevation=None,
            distance_km=0.0,
            data_source="OpenMeteo"
        )
    
    def validate_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> bool:
        """Check if date range is valid for OpenMeteo."""
        # OpenMeteo has data from 1940 to present
        min_date = date(1940, 1, 1)
        max_date = datetime.now().date()
        
        # Cannot request future data
        if end_date > max_date:
            return False
        
        # Check historical data availability
        if start_date < min_date:
            return False
        
        # Check date range is not too long (max 1 year per request)
        if (end_date - start_date).days > 365:
            return False
        
        return True
    
    def get_api_limits(self) -> Dict[str, Any]:
        """Get OpenMeteo API limits."""
        if self.api_key:
            # Commercial tier limits
            return {
                'requests_per_hour': 10000,
                'requests_per_day': 100000,
                'max_date_range_days': 365,
                'historical_data_available': True,
                'data_from_year': 1940
            }
        else:
            # Free tier limits
            return {
                'requests_per_hour': 1000,
                'requests_per_day': 10000,
                'max_date_range_days': 365,
                'historical_data_available': True,
                'data_from_year': 1940
            }


class NOAAProvider(WeatherDataProvider):
    """NOAA weather data provider implementation (placeholder)."""
    
    def __init__(self):
        """Initialize NOAA provider."""
        self.base_url = "https://www.ncei.noaa.gov/data/"
        logger.info("NOAA provider initialized (implementation pending)")
    
    async def get_monthly_average(
        self,
        latitude: float,
        longitude: float,
        year: int,
        month: int
    ) -> Optional[float]:
        """Get monthly average from NOAA (not implemented)."""
        logger.warning("NOAA provider not yet implemented")
        return None
    
    async def get_daily_temperatures(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date
    ) -> List[float]:
        """Get daily temperatures from NOAA (not implemented)."""
        logger.warning("NOAA provider not yet implemented")
        return []
    
    async def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        year: int,
        month: int
    ) -> Optional[WeatherData]:
        """Get weather data from NOAA (not implemented)."""
        logger.warning("NOAA provider not yet implemented")
        return None
    
    def get_nearest_station(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 100.0
    ) -> Optional[WeatherStation]:
        """Find nearest NOAA station (not implemented)."""
        logger.warning("NOAA station search not yet implemented")
        return None
    
    def validate_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> bool:
        """Validate date range for NOAA."""
        # NOAA has extensive historical data
        min_date = date(1900, 1, 1)
        max_date = datetime.now().date()
        
        return start_date >= min_date and end_date <= max_date