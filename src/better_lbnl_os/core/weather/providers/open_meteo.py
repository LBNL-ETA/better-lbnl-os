"""OpenMeteo weather data provider implementation."""

import logging
from datetime import date, datetime
from typing import Any

import pandas as pd
import requests
from requests.exceptions import RequestException

from better_lbnl_os.core.weather.interfaces import WeatherDataProvider
from better_lbnl_os.models.weather import WeatherData, WeatherStation
from better_lbnl_os.utils.calculations import calculate_monthly_average

logger = logging.getLogger(__name__)


class OpenMeteoProvider(WeatherDataProvider):
    """OpenMeteo weather data provider implementation."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        if api_key:
            self.base_url = "https://customer-archive-api.open-meteo.com/v1/archive"
        else:
            self.base_url = "https://archive-api.open-meteo.com/v1/archive"

    def get_monthly_average(
        self, latitude: float, longitude: float, year: int, month: int
    ) -> float | None:
        try:
            weather_data = self.get_weather_data(latitude, longitude, year, month)
            if weather_data:
                return weather_data.avg_temp_c
            return None
        except Exception as e:
            logger.error(f"Error getting monthly average from OpenMeteo: {e}")
            return None

    def get_daily_temperatures(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> list[float]:
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily": "temperature_2m_mean",
                "timezone": "UTC",
            }
            if self.api_key:
                params["apikey"] = self.api_key
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            if "daily" in data and "temperature_2m_mean" in data["daily"]:
                return data["daily"]["temperature_2m_mean"]
            return []
        except RequestException as e:
            logger.error(f"Error fetching daily temps from OpenMeteo: {e}")
            return []

    def get_weather_data(
        self, latitude: float, longitude: float, year: int, month: int
    ) -> WeatherData | None:
        try:
            if not self.validate_date_range(date(year, month, 1), date(year, month, 1)):
                logger.warning(f"Invalid date range for OpenMeteo: {year}-{month}")
                return None

            start_date = pd.Timestamp(year, month, 1)
            end_date = (
                pd.Timestamp(year + 1, 1, 1) - pd.Timedelta(days=1)
                if month == 12
                else pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)
            )

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "hourly": "temperature_2m",
                "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean",
                "timezone": "UTC",
            }
            if self.api_key:
                params["apikey"] = self.api_key

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "hourly" in data and "temperature_2m" in data["hourly"]:
                hourly_temps = data["hourly"]["temperature_2m"]
                avg_temp_c = calculate_monthly_average(hourly_temps)
            else:
                logger.warning("No hourly data in OpenMeteo response")
                return None

            min_temp = None
            max_temp = None
            if "daily" in data:
                daily_data = data["daily"]
                if "temperature_2m_mean" in daily_data:
                    daily_data["temperature_2m_mean"]
                if "temperature_2m_min" in daily_data:
                    mins = [t for t in daily_data["temperature_2m_min"] if t is not None]
                    min_temp = min(mins) if mins else None
                if "temperature_2m_max" in daily_data:
                    maxs = [t for t in daily_data["temperature_2m_max"] if t is not None]
                    max_temp = max(maxs) if maxs else None

            weather = WeatherData(
                latitude=latitude,
                longitude=longitude,
                year=year,
                month=month,
                avg_temp_c=avg_temp_c,
                min_temp_c=min_temp,
                max_temp_c=max_temp,
                data_source="OpenMeteo",
            )
            logger.debug(
                f"Retrieved weather data from OpenMeteo: {year}-{month}, avg: {avg_temp_c:.1f}°C"
            )
            return weather
        except RequestException as e:
            logger.error(f"OpenMeteo API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing OpenMeteo data: {e}")
            return None

    def get_nearest_station(
        self, latitude: float, longitude: float, max_distance_km: float = 100.0
    ) -> WeatherStation | None:
        return WeatherStation(
            station_id=f"GRID_{latitude:.2f}_{longitude:.2f}",
            name=f"OpenMeteo Grid Point ({latitude:.2f}, {longitude:.2f})",
            latitude=latitude,
            longitude=longitude,
            elevation=None,
            distance_km=0.0,
            data_source="OpenMeteo",
        )

    def validate_date_range(self, start_date: date, end_date: date) -> bool:
        min_date = date(1940, 1, 1)
        max_date = datetime.now().date()
        if end_date > max_date:
            return False
        if start_date < min_date:
            return False
        if (end_date - start_date).days > 365:
            return False
        return True

    def get_api_limits(self) -> dict[str, Any]:
        if self.api_key:
            return {
                "requests_per_hour": 10000,
                "requests_per_day": 100000,
                "max_date_range_days": 365,
                "historical_data_available": True,
                "data_from_year": 1940,
            }
        else:
            return {
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "max_date_range_days": 365,
                "historical_data_available": True,
                "data_from_year": 1940,
            }

    def get_weather_data_batch(
        self,
        latitude: float,
        longitude: float,
        start_year: int,
        start_month: int,
        end_year: int,
        end_month: int,
    ) -> list[WeatherData]:
        """Fetch weather data for multiple months in a single API request.

        This is an optimized batch method that makes one HTTP request instead of
        N separate requests for N months of data.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_year: Start year
            start_month: Start month (1-12)
            end_year: End year
            end_month: End month (1-12)

        Returns:
            List of WeatherData objects, one per month
        """
        try:
            # Calculate the full date range
            start_date = pd.Timestamp(start_year, start_month, 1)

            # Calculate end date (last day of end_month)
            if end_month == 12:
                end_date = pd.Timestamp(end_year + 1, 1, 1) - pd.Timedelta(days=1)
            else:
                end_date = pd.Timestamp(end_year, end_month + 1, 1) - pd.Timedelta(days=1)

            # Validate date range
            if not self.validate_date_range(start_date.date(), end_date.date()):
                logger.warning(
                    f"Invalid date range for batch request: {start_date.date()} to {end_date.date()}"
                )
                return []

            # Make single API request for entire range
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "hourly": "temperature_2m",
                "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean",
                "timezone": "UTC",
            }
            if self.api_key:
                params["apikey"] = self.api_key

            logger.info(
                f"Fetching batch weather data from {start_date.date()} to {end_date.date()}"
            )
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Extract hourly and daily data
            if "hourly" not in data or "temperature_2m" not in data["hourly"]:
                logger.warning("No hourly temperature data in batch response")
                return []

            hourly_times = pd.to_datetime(data["hourly"]["time"])
            hourly_temps = data["hourly"]["temperature_2m"]

            daily_data = data.get("daily", {})
            daily_times = pd.to_datetime(daily_data.get("time", []))
            daily_mins = daily_data.get("temperature_2m_min", [])
            daily_maxs = daily_data.get("temperature_2m_max", [])

            # Split data into monthly chunks
            weather_list = []
            current_year = start_year
            current_month = start_month

            while (current_year < end_year) or (
                current_year == end_year and current_month <= end_month
            ):
                # Filter hourly data for this month
                month_mask = (hourly_times.year == current_year) & (
                    hourly_times.month == current_month
                )
                month_hourly_temps = [
                    t for t, m in zip(hourly_temps, month_mask, strict=False) if m and t is not None
                ]

                if not month_hourly_temps:
                    logger.warning(f"No hourly data for {current_year}-{current_month:02d}")
                    current_month += 1
                    if current_month > 12:
                        current_month = 1
                        current_year += 1
                    continue

                # Calculate monthly average
                avg_temp_c = calculate_monthly_average(month_hourly_temps)

                # Filter daily data for this month to get min/max
                if len(daily_times) > 0:
                    daily_month_mask = (daily_times.year == current_year) & (
                        daily_times.month == current_month
                    )
                    month_mins = [
                        t
                        for t, m in zip(daily_mins, daily_month_mask, strict=False)
                        if m and t is not None
                    ]
                    month_maxs = [
                        t
                        for t, m in zip(daily_maxs, daily_month_mask, strict=False)
                        if m and t is not None
                    ]
                    min_temp = min(month_mins) if month_mins else None
                    max_temp = max(month_maxs) if month_maxs else None
                else:
                    min_temp = None
                    max_temp = None

                # Create WeatherData object for this month
                weather = WeatherData(
                    latitude=latitude,
                    longitude=longitude,
                    year=current_year,
                    month=current_month,
                    avg_temp_c=avg_temp_c,
                    min_temp_c=min_temp,
                    max_temp_c=max_temp,
                    data_source="OpenMeteo",
                )
                weather_list.append(weather)

                logger.debug(
                    f"Processed batch data for {current_year}-{current_month:02d}, "
                    f"avg: {avg_temp_c:.1f}°C"
                )

                # Move to next month
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1

            logger.info(f"Successfully fetched {len(weather_list)} months in single batch request")
            return weather_list

        except RequestException as e:
            logger.error(f"OpenMeteo batch API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing OpenMeteo batch data: {e}")
            return []
