"""
Pure geocoding algorithms extracted from the BETTER Django application.

This module provides functions for geocoding addresses using Google Maps API
and related location utilities, without any Django dependencies.
"""
import logging
from typing import Tuple, Optional

import geocoder
import numpy as np
from better_lbnl.domain.models import LocationInfo
from better_lbnl.utils.geography import haversine_distance

logger = logging.getLogger(__name__)


def geocode_address(address: str, api_key: str) -> LocationInfo:
    """
    Geocode an address using Google Maps API and return location information.
    
    This function is a pure function that takes an address string and API key,
    geocodes it using Google Maps, and returns structured location data.
    
    Args:
        address: Address string or zip code to geocode
        api_key: Google Maps API key
        
    Returns:
        LocationInfo dataclass with geocoded location data
        
    Raises:
        ValueError: If address is invalid format
        Exception: If geocoding fails or API request is denied
    """
    logger.debug(f'Geocoding address: {address}')
    
    if not isinstance(address, (str, int)):
        raise ValueError(f"Invalid address: {address}. "
                        f"Value must be a string or integer (zip code).")
    
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
            raise Exception("Google Maps API denied geocoding request")
            
        lat, lng = g.latlng
        zipcode = g.postal
        country_code = g.country
        
        # Extract state for US addresses
        if country_code == 'US':
            state = g.state
        else:
            state = 'INT'
            
    except Exception as e:
        logger.exception(f"Could not geocode location: {e}")
        raise Exception(f'Cannot geocode location: {address}. '
                       f'Please check your building address and provide more details.') from e
    
    return LocationInfo(
        geo_lat=lat,
        geo_lng=lng,
        zipcode=zipcode,
        state=state,
        country_code=country_code
    )


def find_closest_weather_station(
    latitude: float, 
    longitude: float,
    weather_stations: list
) -> Tuple[str, str]:
    """
    Find the closest weather station to given coordinates.
    
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
        
    min_distance = float('inf')
    closest_station_id = None
    closest_station_name = None
    
    for station in weather_stations:
        distance = haversine_distance(
            latitude, longitude,
            station['latitude'], station['longitude']
        )
        
        if distance < min_distance:
            min_distance = distance
            closest_station_id = station['station_ID']
            closest_station_name = station['station_name']
    
    return closest_station_id, closest_station_name


def find_egrid_subregion(zipcode: str, egrid_mapping: dict) -> str:
    """
    Find the eGrid emission subregion for a US zip code.
    
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
        logger.info(f"Could not transform zipcode to int: {zipcode}. "
                   f"Returning 'OTHERS'...")
        return "OTHERS"
    
    # Check for special region codes first (e.g., Berkeley, CA)
    special_region = _check_special_regions(zipcode)
    if special_region != 'OTHERS':
        return special_region
    
    # Look up in eGrid mapping
    return egrid_mapping.get(zipcode_int, "OTHERS")


def _check_special_regions(zipcode: str) -> str:
    """
    Check if zipcode corresponds to a special emission region.
    
    Args:
        zipcode: Zip code string
        
    Returns:
        Special region code or 'OTHERS'
    """
    # Berkeley, CA special zipcodes
    berkeley_zipcodes = [
        '94701', '94702', '94703', '94704', '94705', '94706',
        '94707', '94708', '94709', '94710', '94712', '94720'
    ]
    
    if zipcode and str(zipcode) in berkeley_zipcodes:
        return 'SPECIAL_BERKELEY'
    
    return 'OTHERS'


def create_dummy_location_info() -> LocationInfo:
    """
    Create dummy location info for testing/fallback purposes.
    
    Returns:
        LocationInfo for San Francisco International Airport
    """
    return LocationInfo(
        geo_lat=37.77712,
        geo_lng=-122.41964,
        zipcode="94102",
        state="CA",
        country_code="US"
    )