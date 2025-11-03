"""Weather provider interfaces (ABCs).

Defines contracts for pluggable weather data providers.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from better_lbnl_os.models.weather import WeatherData, WeatherStation


class WeatherDataProvider(ABC):
    """Abstract interface for weather data providers."""

    @abstractmethod
    def get_monthly_average(
        self,
        latitude: float,
        longitude: float,
        year: int,
        month: int,
    ) -> float | None:
        """Monthly average temperature in Celsius, or None if unavailable."""
        raise NotImplementedError

    @abstractmethod
    def get_daily_temperatures(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[float]:
        """List of daily average temperatures in Celsius."""
        raise NotImplementedError

    @abstractmethod
    def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        year: int,
        month: int,
    ) -> WeatherData | None:
        """Complete weather data for a month, or None if unavailable."""
        raise NotImplementedError

    @abstractmethod
    def get_nearest_station(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 100.0,
    ) -> WeatherStation | None:
        """Nearest station to a location, or None if none within range."""
        raise NotImplementedError

    @abstractmethod
    def validate_date_range(self, start_date: date, end_date: date) -> bool:
        """Return True if date range is valid for this provider."""
        raise NotImplementedError

    def get_provider_name(self) -> str:
        return self.__class__.__name__.replace("Provider", "")

    def get_api_limits(self) -> dict[str, Any]:
        return {
            "requests_per_hour": None,
            "requests_per_day": None,
            "max_date_range_days": None,
            "historical_data_available": True,
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
        """Get weather data for a date range in a single batch request.

        This is an optional optimization method. Providers that support batch
        fetching can override this to make fewer API calls. If not overridden,
        the service will fall back to month-by-month fetching.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_year: Start year
            start_month: Start month (1-12)
            end_year: End year
            end_month: End month (1-12)

        Returns:
            List of WeatherData objects, one per month in the range
        """
        # Default implementation: not supported, return empty list
        # Services should fall back to month-by-month fetching
        return []
