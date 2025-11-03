"""Weather domain models."""

from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    """Domain model for weather data with calculation methods."""

    station_id: str | None = Field(None, description="Weather station identifier")
    latitude: float = Field(..., description="Station latitude")
    longitude: float = Field(..., description="Station longitude")
    year: int = Field(..., description="Year of observation")
    month: int = Field(..., ge=1, le=12, description="Month of observation")
    avg_temp_c: float = Field(..., description="Monthly average temperature in Celsius")
    min_temp_c: float | None = Field(None, description="Minimum temperature in Celsius")
    max_temp_c: float | None = Field(None, description="Maximum temperature in Celsius")
    data_source: str = Field(default="OpenMeteo", description="Data source (NOAA, OpenMeteo, etc.)")

    @property
    def avg_temp_f(self) -> float:
        """Get average temperature in Fahrenheit."""
        from better_lbnl_os.utils.calculations import celsius_to_fahrenheit

        return celsius_to_fahrenheit(self.avg_temp_c)

    @property
    def min_temp_f(self) -> float | None:
        """Get minimum temperature in Fahrenheit."""
        if self.min_temp_c is not None:
            from better_lbnl_os.utils.calculations import celsius_to_fahrenheit

            return celsius_to_fahrenheit(self.min_temp_c)
        return None

    @property
    def max_temp_f(self) -> float | None:
        """Get maximum temperature in Fahrenheit."""
        if self.max_temp_c is not None:
            from better_lbnl_os.utils.calculations import celsius_to_fahrenheit

            return celsius_to_fahrenheit(self.max_temp_c)
        return None


class WeatherSeries(BaseModel):
    """Monthly weather time series aligned to calendar months."""

    months: list[__import__("datetime").date] = Field(
        default_factory=list, description="List of YYYY-MM-01 dates"
    )
    degC: list[float] = Field(default_factory=list, description="Monthly average temperature in °C")
    degF: list[float] = Field(default_factory=list, description="Monthly average temperature in °F")


class WeatherStation(BaseModel):
    """Domain model for weather station information."""

    station_id: str = Field(..., description="Station identifier (e.g., NOAA ID)")
    name: str = Field(..., description="Station name")
    latitude: float = Field(..., ge=-90, le=90, description="Station latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Station longitude")
    elevation: float | None = Field(None, description="Station elevation in meters")
    distance_km: float | None = Field(None, description="Distance from target location in km")
    data_source: str = Field(default="NOAA", description="Data source")

    def distance_to(self, lat: float, lng: float) -> float:
        """Calculate distance to a given latitude/longitude.

        Args:
            lat: Target latitude
            lng: Target longitude

        Returns:
            Distance in kilometers
        """
        from better_lbnl_os.utils.geography import haversine_distance

        return haversine_distance(self.latitude, self.longitude, lat, lng)


__all__ = ["WeatherData", "WeatherSeries", "WeatherStation"]
