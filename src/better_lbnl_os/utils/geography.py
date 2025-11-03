"""Unified geography and geocoding utilities for building energy analysis.

This module provides comprehensive geographic functionality including:
- Basic geographic calculations (haversine distance, coordinate validation)
- Geocoding services using Google Maps API
- Location data enrichment (weather stations, eGrid regions)
- Geographic utility functions
"""

import logging
import math

import geocoder

from better_lbnl_os.models import LocationInfo

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0


# =============================================================================
# BASIC GEOGRAPHIC CALCULATIONS
# =============================================================================


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the haversine distance between two coordinate points.

    This function calculates the great-circle distance between two points
    on the Earth's surface given their latitude and longitude coordinates.

    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees

    Returns:
        Distance between the points in kilometers
    """
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2

    c = 2 * math.asin(math.sqrt(a))

    return EARTH_RADIUS_KM * c


def is_valid_coordinates(latitude: float, longitude: float) -> bool:
    """Check if latitude and longitude coordinates are valid.

    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees

    Returns:
        True if coordinates are within valid ranges
    """
    return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * math.pi / 180


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees."""
    return radians * 180 / math.pi


# =============================================================================
# GEOCODING SERVICES
# =============================================================================


def geocode(address: str, api_key: str, weather_stations: list | None = None) -> LocationInfo:
    """Main geocoding function that provides complete location information.

    This function geocodes an address using Google Maps API and enriches it with:
    - Weather station information
    - eGrid subregion for emissions calculations
    - State and country information

    Args:
        address: Address string or zip code to geocode
        api_key: Google Maps API key
        weather_stations: List of weather station data (optional)

    Returns:
        LocationInfo with complete geocoded location data

    Raises:
        ValueError: If address is invalid format
        Exception: If geocoding fails or API request is denied
    """
    logger.debug(f"Geocoding address: {address}")

    if not isinstance(address, (str, int)):
        raise ValueError(
            f"Invalid address: {address}. " f"Value must be a string or integer (zip code)."
        )

    try:
        # Use Google Maps geocoding
        g = geocoder.google(address, key=api_key)

        # Handle cases where postal code is missing
        if g.postal is None:
            if g.json:
                g = geocoder.google(g.latlng, method="reverse", key=api_key)
            else:
                g = geocoder.google(address, method="reverse", key=api_key)

        if g.error == "REQUEST_DENIED":
            # Don't wrap API denial errors - let them propagate directly
            raise Exception("Google Maps API denied geocoding request")

        lat, lng = g.latlng
        zipcode = g.postal
        country_code = g.country

        # Extract state for US addresses
        if country_code == "US":
            state = g.state
        else:
            state = "INT"

    except Exception as e:
        # If it's an API denial, re-raise without wrapping
        if "Google Maps API denied" in str(e):
            raise
        # Otherwise wrap with helpful message
        logger.exception(f"Could not geocode location: {e}")
        raise Exception(
            f"Cannot geocode location: {address}. "
            f"Please check your building address and provide more details."
        ) from e

    # Find closest weather station
    noaa_station_id = None
    noaa_station_name = None
    if weather_stations:
        try:
            noaa_station_id, noaa_station_name = find_closest_weather_station(
                lat, lng, weather_stations
            )
        except Exception as e:
            logger.warning(f"Could not find weather station: {e}")

    # Look for eGrid region
    egrid_sub_region = None
    if country_code == "US":
        if zipcode:
            try:
                # Create a basic eGrid mapping - in production this would be comprehensive
                egrid_mapping = {}  # Would be loaded from constants or database
                egrid_sub_region = find_egrid_subregion(zipcode, egrid_mapping)
            except Exception as e:
                logger.info(f"Exception finding eGrid subregion: {e}")
                egrid_sub_region = country_code
        else:
            egrid_sub_region = country_code
    else:
        egrid_sub_region = country_code

    return LocationInfo(
        geo_lat=lat,
        geo_lng=lng,
        zipcode=zipcode,
        state=state,
        country_code=country_code,
        noaa_station_id=noaa_station_id,
        noaa_station_name=noaa_station_name,
        egrid_sub_region=egrid_sub_region,
    )


def find_closest_weather_station(
    latitude: float, longitude: float, weather_stations: list
) -> tuple[str, str]:
    """Find the closest weather station to given coordinates.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        weather_stations: List of weather station dictionaries with
                         'latitude', 'longitude', 'station_ID', 'station_name'

    Returns:
        Tuple of (station_ID, station_name) for closest station
    """
    if not weather_stations:
        raise ValueError("Weather stations list cannot be empty")

    min_distance = float("inf")
    closest_station_id = None
    closest_station_name = None

    for station in weather_stations:
        distance = haversine_distance(
            latitude, longitude, station["latitude"], station["longitude"]
        )

        if distance < min_distance:
            min_distance = distance
            closest_station_id = station["station_ID"]
            closest_station_name = station["station_name"]

    return closest_station_id, closest_station_name


# =============================================================================
# EGRID REGION UTILITIES
# =============================================================================


def find_egrid_subregion(zipcode: str, egrid_mapping: dict) -> str:
    """Find the eGrid emission subregion for a US zip code.

    Args:
        zipcode: Five digit US zip code (can include dash extension)
        egrid_mapping: Dictionary mapping zip codes to eGrid subregions

    Returns:
        eGrid subregion code, or 'OTHERS' if not found

    Raises:
        ValueError: If zipcode is invalid format
    """
    if not zipcode:
        raise ValueError("Must provide zipcode argument")

    # Handle extended zip codes (e.g., "12345-6789")
    if isinstance(zipcode, str) and "-" in zipcode:
        zipcode = zipcode.split("-")[0]

    try:
        zipcode_int = int(zipcode)
    except (ValueError, TypeError):
        logger.info(f"Could not transform zipcode to int: {zipcode}. " f"Returning 'OTHERS'...")
        return "OTHERS"

    # Check for special region codes first (e.g., Berkeley, CA)
    special_region = _check_special_regions(zipcode)
    if special_region != "OTHERS":
        return special_region

    # Look up in eGrid mapping
    return egrid_mapping.get(zipcode_int, "OTHERS")


def _check_special_regions(zipcode: str) -> str:
    """Check if zipcode corresponds to a special emission region.

    Args:
        zipcode: Zip code string

    Returns:
        Special region code or 'OTHERS'
    """
    # Berkeley, CA special zipcodes
    berkeley_zipcodes = [
        "94701",
        "94702",
        "94703",
        "94704",
        "94705",
        "94706",
        "94707",
        "94708",
        "94709",
        "94710",
        "94712",
        "94720",
    ]

    if zipcode and str(zipcode) in berkeley_zipcodes:
        return "SPECIAL_BERKELEY"

    return "OTHERS"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_dummy_location_info() -> LocationInfo:
    """Create dummy location info for testing/fallback purposes.

    Returns:
        LocationInfo for San Francisco International Airport
    """
    return LocationInfo(
        geo_lat=37.77712,
        geo_lng=-122.41964,
        zipcode="94102",
        state="CA",
        country_code="US",
        noaa_station_id="724940-23234",
        noaa_station_name="SAN FRANCISCO INTERNATIONAL AIRPORT",
        egrid_sub_region="CAMX",
    )
