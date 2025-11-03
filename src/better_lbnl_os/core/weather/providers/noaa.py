"""NOAA weather data provider implementation (placeholder)."""

import logging
from datetime import date, datetime

from better_lbnl_os.core.weather.interfaces import WeatherDataProvider
from better_lbnl_os.models.weather import WeatherData, WeatherStation

logger = logging.getLogger(__name__)


class NOAAProvider(WeatherDataProvider):
    """NOAA weather data provider implementation (placeholder)."""

    def __init__(self):
        self.base_url = "https://www.ncei.noaa.gov/data/"
        logger.info("NOAA provider initialized (implementation pending)")

    def get_monthly_average(
        self, latitude: float, longitude: float, year: int, month: int
    ) -> float | None:
        logger.warning("NOAA provider not yet implemented")
        return None

    def get_daily_temperatures(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> list[float]:
        logger.warning("NOAA provider not yet implemented")
        return []

    def get_weather_data(
        self, latitude: float, longitude: float, year: int, month: int
    ) -> WeatherData | None:
        logger.warning("NOAA provider not yet implemented")
        return None

    def get_nearest_station(
        self, latitude: float, longitude: float, max_distance_km: float = 100.0
    ) -> WeatherStation | None:
        logger.warning("NOAA station search not yet implemented")
        return None

    def validate_date_range(self, start_date: date, end_date: date) -> bool:
        min_date = date(1900, 1, 1)
        max_date = datetime.now().date()
        return start_date >= min_date and end_date <= max_date
