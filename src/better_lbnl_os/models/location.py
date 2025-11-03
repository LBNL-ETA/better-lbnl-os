"""Location info domain model."""

from pydantic import BaseModel, Field


class LocationInfo(BaseModel):
    """Domain model for geocoded location information."""

    geo_lat: float = Field(..., description="Latitude coordinate")
    geo_lng: float = Field(..., description="Longitude coordinate")
    zipcode: str | None = Field(None, description="Postal/ZIP code")
    state: str | None = Field(None, description="State or province")
    country_code: str = Field(default="US", description="ISO country code")
    noaa_station_id: str | None = Field(None, description="NOAA weather station ID")
    noaa_station_name: str | None = Field(None, description="NOAA weather station name")
    egrid_sub_region: str | None = Field(None, description="eGrid subregion for emissions")

    def is_valid_coordinates(self) -> bool:
        """Check if coordinates are within valid latitude/longitude ranges.

        Returns:
            True if coordinates are valid, False otherwise
        """
        return (-90 <= self.geo_lat <= 90) and (-180 <= self.geo_lng <= 180)

    def calculate_distance_to(self, other: "LocationInfo") -> float:
        """Calculate distance to another location.

        Args:
            other: Another LocationInfo object

        Returns:
            Distance in kilometers
        """
        from better_lbnl_os.utils.geography import haversine_distance

        return haversine_distance(self.geo_lat, self.geo_lng, other.geo_lat, other.geo_lng)


class LocationSummary(BaseModel):
    """Normalized location metadata for pricing/emission lookups."""

    country_code: str = Field(default="US", description="ISO country code")
    state_code: str | None = Field(default=None, description="Two-letter state/province code")
    zipcode: str | None = Field(default=None, description="Postal/ZIP code")
    egrid_subregion: str | None = Field(default=None, description="eGrid subregion identifier")

    def to_metadata(self) -> dict[str, str | None]:
        """Return a dict view excluding unset fields."""
        return self.model_dump(exclude_none=True)


__all__ = ["LocationInfo", "LocationSummary"]
