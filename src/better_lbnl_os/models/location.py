"""Location info domain model."""

from typing import Optional
from pydantic import BaseModel, Field


class LocationInfo(BaseModel):
    """Domain model for geocoded location information."""

    geo_lat: float = Field(..., description="Latitude coordinate")
    geo_lng: float = Field(..., description="Longitude coordinate")
    zipcode: Optional[str] = Field(None, description="Postal/ZIP code")
    state: Optional[str] = Field(None, description="State or province")
    country_code: str = Field(default="US", description="ISO country code")
    noaa_station_id: Optional[str] = Field(None, description="NOAA weather station ID")
    noaa_station_name: Optional[str] = Field(None, description="NOAA weather station name")
    egrid_sub_region: Optional[str] = Field(None, description="eGrid subregion for emissions")

    def is_valid_coordinates(self) -> bool:
        return (-90 <= self.geo_lat <= 90) and (-180 <= self.geo_lng <= 180)

    def calculate_distance_to(self, other: "LocationInfo") -> float:
        from better_lbnl_os.utils.geography import haversine_distance

        return haversine_distance(self.geo_lat, self.geo_lng, other.geo_lat, other.geo_lng)


__all__ = ["LocationInfo"]
