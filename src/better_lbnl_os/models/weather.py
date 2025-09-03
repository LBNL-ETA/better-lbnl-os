"""Weather domain models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    """Domain model for weather data with calculation methods."""

    station_id: Optional[str] = Field(None, description="Weather station identifier")
    latitude: float = Field(..., description="Station latitude")
    longitude: float = Field(..., description="Station longitude")
    year: int = Field(..., description="Year of observation")
    month: int = Field(..., ge=1, le=12, description="Month of observation")
    avg_temp_c: float = Field(..., description="Monthly average temperature in Celsius")
    min_temp_c: Optional[float] = Field(None, description="Minimum temperature in Celsius")
    max_temp_c: Optional[float] = Field(None, description="Maximum temperature in Celsius")
    data_source: str = Field(default="OpenMeteo", description="Data source (NOAA, OpenMeteo, etc.)")
    daily_temps_c: Optional[List[float]] = Field(None, description="Daily temperatures for the month")

    @property
    def avg_temp_f(self) -> float:
        from better_lbnl_os.utils.calculations import celsius_to_fahrenheit

        return celsius_to_fahrenheit(self.avg_temp_c)

    @property
    def min_temp_f(self) -> Optional[float]:
        if self.min_temp_c is not None:
            from better_lbnl_os.utils.calculations import celsius_to_fahrenheit

            return celsius_to_fahrenheit(self.min_temp_c)
        return None

    @property
    def max_temp_f(self) -> Optional[float]:
        if self.max_temp_c is not None:
            from better_lbnl_os.utils.calculations import celsius_to_fahrenheit

            return celsius_to_fahrenheit(self.max_temp_c)
        return None

    def calculate_hdd(self, base_temp_f: float = 65.0, use_daily: bool = True) -> float:
        from better_lbnl_os.utils.calculations import (
            calculate_heating_degree_days,
            estimate_monthly_hdd,
            convert_temperature_list,
        )
        import calendar

        if use_daily and self.daily_temps_c:
            daily_temps_f = convert_temperature_list(self.daily_temps_c, "C", "F")
            return calculate_heating_degree_days(daily_temps_f, base_temp_f, "F")
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        return estimate_monthly_hdd(self.avg_temp_f, days_in_month, base_temp_f)

    def calculate_cdd(self, base_temp_f: float = 65.0, use_daily: bool = True) -> float:
        from better_lbnl_os.utils.calculations import (
            calculate_cooling_degree_days,
            estimate_monthly_cdd,
            convert_temperature_list,
        )
        import calendar

        if use_daily and self.daily_temps_c:
            daily_temps_f = convert_temperature_list(self.daily_temps_c, "C", "F")
            return calculate_cooling_degree_days(daily_temps_f, base_temp_f, "F")
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        return estimate_monthly_cdd(self.avg_temp_f, days_in_month, base_temp_f)

    def is_valid_temperature(self) -> bool:
        from better_lbnl_os.utils.calculations import validate_temperature_range

        return validate_temperature_range(self.avg_temp_c)


class WeatherStation(BaseModel):
    """Domain model for weather station information."""

    station_id: str = Field(..., description="Station identifier (e.g., NOAA ID)")
    name: str = Field(..., description="Station name")
    latitude: float = Field(..., ge=-90, le=90, description="Station latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Station longitude")
    elevation: Optional[float] = Field(None, description="Station elevation in meters")
    distance_km: Optional[float] = Field(None, description="Distance from target location in km")
    data_source: str = Field(default="NOAA", description="Data source")

    def distance_to(self, lat: float, lng: float) -> float:
        from better_lbnl_os.utils.geography import haversine_distance

        return haversine_distance(self.latitude, self.longitude, lat, lng)


__all__ = ["WeatherData", "WeatherStation"]
