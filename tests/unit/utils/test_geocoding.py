"""
Tests for geocoding algorithms.
"""

from unittest.mock import Mock, patch

import pytest

from better_lbnl_os.models import LocationInfo
from better_lbnl_os.utils.geography import (
    _check_special_regions,
    create_dummy_location_info,
    find_closest_weather_station,
    find_egrid_subregion,
    geocode,
)


class TestGeocoding:
    """Test suite for geocoding functionality."""

    @patch("better_lbnl_os.utils.geography.geocoder")
    def test_geocode_success(self, mock_geocoder):
        """Test successful address geocoding."""
        # Mock the geocoder response
        mock_result = Mock()
        mock_result.latlng = [37.7749, -122.4194]
        mock_result.postal = "94102"
        mock_result.country = "US"
        mock_result.state = "CA"
        mock_result.error = None
        mock_geocoder.google.return_value = mock_result

        api_key = "test_api_key"
        address = "San Francisco, CA"

        result = geocode(address, api_key)

        assert isinstance(result, LocationInfo)
        assert result.geo_lat == 37.7749
        assert result.geo_lng == -122.4194
        assert result.zipcode == "94102"
        assert result.country_code == "US"
        assert result.state == "CA"

        # Verify geocoder was called correctly
        mock_geocoder.google.assert_called_with(address, key=api_key)

    @patch("better_lbnl_os.utils.geography.geocoder")
    def test_geocode_api_denied(self, mock_geocoder):
        """Test geocoding when API request is denied."""
        # Mock the geocoder response with API denial
        mock_result = Mock()
        mock_result.error = "REQUEST_DENIED"
        mock_geocoder.google.return_value = mock_result

        api_key = "invalid_api_key"
        address = "San Francisco, CA"

        with pytest.raises(Exception, match="Google Maps API denied"):
            geocode(address, api_key)

    @patch("better_lbnl_os.utils.geography.geocoder")
    def test_geocode_international(self, mock_geocoder):
        """Test geocoding for international address."""
        # Mock the geocoder response for non-US location
        mock_result = Mock()
        mock_result.latlng = [51.5074, -0.1278]
        mock_result.postal = "SW1A 1AA"
        mock_result.country = "GB"
        mock_result.state = None
        mock_result.error = None
        mock_geocoder.google.return_value = mock_result

        api_key = "test_api_key"
        address = "London, UK"

        result = geocode(address, api_key)

        assert result.country_code == "GB"
        assert result.state == "INT"  # Should be set to 'INT' for non-US

    def test_geocode_invalid_address_type(self):
        """Test geocoding with invalid address type."""
        api_key = "test_api_key"
        invalid_address = []  # List instead of string

        with pytest.raises(ValueError, match="Invalid address"):
            geocode(invalid_address, api_key)


class TestWeatherStationFinder:
    """Test suite for weather station finding functionality."""

    def test_find_closest_weather_station(self):
        """Test finding closest weather station."""
        # Mock weather stations data
        weather_stations = [
            {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "station_ID": "SFO",
                "station_name": "San Francisco International Airport",
            },
            {
                "latitude": 37.6213,
                "longitude": -122.3790,
                "station_ID": "SJC",
                "station_name": "San Jose Airport",
            },
            {
                "latitude": 38.5816,
                "longitude": -121.4944,
                "station_ID": "SAC",
                "station_name": "Sacramento Airport",
            },
        ]

        # Test coordinates closer to San Francisco
        latitude = 37.8000
        longitude = -122.4000

        station_id, station_name = find_closest_weather_station(
            latitude, longitude, weather_stations
        )

        assert station_id == "SFO"
        assert station_name == "San Francisco International Airport"

    def test_find_closest_weather_station_empty_list(self):
        """Test finding weather station with empty stations list."""
        latitude = 37.7749
        longitude = -122.4194
        weather_stations = []

        with pytest.raises(ValueError, match="cannot be empty"):
            find_closest_weather_station(latitude, longitude, weather_stations)


class TestEGridMapping:
    """Test suite for eGrid subregion mapping functionality."""

    def test_find_egrid_subregion_valid_zip(self):
        """Test eGrid subregion lookup with valid zip code."""
        # Mock eGrid mapping data
        egrid_mapping = {94102: "CAMX", 10001: "NYUP", 60601: "RFCM"}

        zipcode = "94102"
        result = find_egrid_subregion(zipcode, egrid_mapping)
        assert result == "CAMX"

    def test_find_egrid_subregion_extended_zip(self):
        """Test eGrid subregion lookup with extended zip code."""
        egrid_mapping = {94102: "CAMX"}

        zipcode = "94102-1234"  # Extended format
        result = find_egrid_subregion(zipcode, egrid_mapping)
        assert result == "CAMX"

    def test_find_egrid_subregion_not_found(self):
        """Test eGrid subregion lookup with unknown zip code."""
        egrid_mapping = {94102: "CAMX"}

        zipcode = "99999"  # Not in mapping
        result = find_egrid_subregion(zipcode, egrid_mapping)
        assert result == "OTHERS"

    def test_find_egrid_subregion_berkeley_special(self):
        """Test eGrid subregion lookup for Berkeley special case."""
        egrid_mapping = {}  # Empty mapping

        zipcode = "94704"  # Berkeley zip code
        result = find_egrid_subregion(zipcode, egrid_mapping)
        assert result == "SPECIAL_BERKELEY"

    def test_find_egrid_subregion_invalid_zip(self):
        """Test eGrid subregion lookup with invalid zip code format."""
        egrid_mapping = {}

        zipcode = "INVALID"
        result = find_egrid_subregion(zipcode, egrid_mapping)
        assert result == "OTHERS"

    def test_find_egrid_subregion_empty_zip(self):
        """Test eGrid subregion lookup with empty zip code."""
        egrid_mapping = {}

        with pytest.raises(ValueError, match="Must provide zipcode"):
            find_egrid_subregion("", egrid_mapping)


class TestSpecialRegions:
    """Test suite for special region identification."""

    def test_check_special_regions_berkeley(self):
        """Test special region check for Berkeley zip codes."""
        berkeley_zips = [
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

        for zipcode in berkeley_zips:
            result = _check_special_regions(zipcode)
            assert result == "SPECIAL_BERKELEY"

    def test_check_special_regions_non_berkeley(self):
        """Test special region check for non-Berkeley zip codes."""
        non_berkeley_zips = ["94102", "10001", "60601", "90210"]

        for zipcode in non_berkeley_zips:
            result = _check_special_regions(zipcode)
            assert result == "OTHERS"

    def test_check_special_regions_none_input(self):
        """Test special region check with None input."""
        result = _check_special_regions(None)
        assert result == "OTHERS"


class TestLocationInfo:
    """Test suite for LocationInfo domain model."""

    def test_create_dummy_location_info(self):
        """Test creation of dummy location info."""
        dummy = create_dummy_location_info()

        assert isinstance(dummy, LocationInfo)
        assert dummy.is_valid_coordinates()
        assert dummy.zipcode == "94102"
        assert dummy.country_code == "US"

    def test_location_info_validation(self):
        """Test LocationInfo coordinate validation."""
        # Valid coordinates
        valid_location = LocationInfo(
            geo_lat=37.7749, geo_lng=-122.4194, zipcode="94102", country_code="US"
        )
        assert valid_location.is_valid_coordinates()

        # Invalid coordinates
        invalid_location = LocationInfo(
            geo_lat=200.0, geo_lng=-122.4194, zipcode="94102", country_code="US"  # Invalid latitude
        )
        assert not invalid_location.is_valid_coordinates()

    def test_location_distance_calculation(self):
        """Test distance calculation between locations."""
        sf = LocationInfo(geo_lat=37.7749, geo_lng=-122.4194, zipcode="94102", country_code="US")

        la = LocationInfo(geo_lat=34.0522, geo_lng=-118.2437, zipcode="90210", country_code="US")

        distance = sf.calculate_distance_to(la)

        # Distance between SF and LA should be approximately 560km
        assert 500 < distance < 600


if __name__ == "__main__":
    pytest.main([__file__])
