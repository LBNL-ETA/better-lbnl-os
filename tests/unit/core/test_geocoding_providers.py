"""Unit tests for GoogleMapsGeocodingProvider."""

import math
from unittest.mock import patch

import pytest

from better_lbnl_os.core.geocoding.providers import GoogleMapsGeocodingProvider
from better_lbnl_os.utils.geography import EARTH_RADIUS_KM, haversine_distance

# Atlanta, GA, and the unrelated Hanoi point Google has returned first
# when reverse-geocoding some US cities.
ATLANTA = (33.7490, -84.3880)
HANOI = (21.158, 105.817)


class FakeGeocodeResult:
    """One geocoder hit, with the attributes the provider reads."""

    def __init__(self, *, latlng, postal, country, state):
        self.latlng = list(latlng)
        self.postal = postal
        self.country = country
        self.state = state


class FakeGeocodeQuery:
    """Iterable geocoder query whose attributes delegate to the first hit."""

    def __init__(self, results):
        self._results = list(results)
        self.error = None

    def __iter__(self):
        return iter(self._results)

    def __bool__(self):
        return bool(self._results)

    def __getattr__(self, name):
        return getattr(self._results[0], name)


def _offset_north(latitude, longitude, distance_km):
    """Return a point ``distance_km`` due north, matching the haversine radius."""
    delta_lat = math.degrees(distance_km / EARTH_RADIUS_KM)
    return [latitude + delta_lat, longitude]


def _geocode(address, forward, reverse_results):
    provider = GoogleMapsGeocodingProvider("test-key")
    calls = []

    def google(query, method=None, key=None):
        calls.append((query, method, key))
        if method == "reverse":
            return FakeGeocodeQuery(reverse_results)
        return FakeGeocodeQuery([forward])

    with patch("better_lbnl_os.core.geocoding.providers.geocoder") as mock_geocoder:
        mock_geocoder.google.side_effect = google
        location = provider.geocode(address)
    return location, calls


def _atlanta_forward(**overrides):
    fields = {
        "latlng": ATLANTA,
        "postal": None,
        "country": "US",
        "state": "Georgia",
    }
    fields.update(overrides)
    return FakeGeocodeResult(**fields)


def test_geocode_uses_forward_result_when_postal_is_present():
    """A forward hit that already has a ZIP code is not replaced or reversed."""
    forward = _atlanta_forward(postal="30303", state="GA")

    location, calls = _geocode("Atlanta, GA", forward, reverse_results=[])

    assert calls == [("Atlanta, GA", None, "test-key")]
    assert location.geo_lat == pytest.approx(ATLANTA[0])
    assert location.geo_lng == pytest.approx(ATLANTA[1])
    assert location.zipcode == "30303"
    assert location.state == "GA"
    assert location.country_code == "US"
    assert location.egrid_sub_region == "SRSO"


def test_geocode_ignores_unrelated_first_reverse_result():
    """Fill ZIP and eGRID from the first reverse hit that is still Atlanta.

    The first reverse result is in another country, which is the failure that
    broke BETTER building creation (better_lbnl#547).
    """
    near = _offset_north(*ATLANTA, 10)
    closer = _offset_north(*ATLANTA, 1)
    outside = _offset_north(*ATLANTA, 26)
    assert haversine_distance(*ATLANTA, *near) < 25
    assert haversine_distance(*ATLANTA, *outside) > 25

    reverse_results = [
        FakeGeocodeResult(latlng=HANOI, postal="100000", country="VN", state="Hà Nội"),
        FakeGeocodeResult(latlng=near, postal=None, country="US", state="GA"),
        FakeGeocodeResult(latlng=near, postal="35203", country="US", state="AL"),
        FakeGeocodeResult(latlng=outside, postal="31401", country="US", state="GA"),
        FakeGeocodeResult(latlng=near, postal="30303", country="United States", state="GA"),
        FakeGeocodeResult(latlng=closer, postal="30301", country="US", state="Georgia"),
    ]

    location, calls = _geocode("Atlanta, GA", _atlanta_forward(), reverse_results)

    assert calls[0] == ("Atlanta, GA", None, "test-key")
    assert calls[1][0] == ATLANTA
    assert calls[1][1:] == ("reverse", "test-key")
    # Coordinates, state, and country stay on the forward result.
    assert location.geo_lat == pytest.approx(ATLANTA[0])
    assert location.geo_lng == pytest.approx(ATLANTA[1])
    assert location.state == "GA"
    assert location.country_code == "US"
    # The first qualifying reverse hit supplies the ZIP and eGRID subregion.
    assert location.zipcode == "30303"
    assert location.egrid_sub_region == "SRSO"


def test_geocode_returns_forward_result_when_no_reverse_hit_qualifies():
    """Leave zipcode empty when every reverse hit fails the place check."""
    near = _offset_north(*ATLANTA, 5)
    outside = _offset_north(*ATLANTA, 40)
    reverse_results = [
        FakeGeocodeResult(latlng=HANOI, postal=None, country="VN", state="Hà Nội"),
        FakeGeocodeResult(latlng=near, postal="   ", country="US", state="GA"),
        FakeGeocodeResult(latlng=near, postal="35203", country="US", state="Alabama"),
        FakeGeocodeResult(latlng=outside, postal="31401", country="USA", state="Georgia"),
    ]

    location, calls = _geocode("Atlanta, GA", _atlanta_forward(), reverse_results)

    assert len(calls) == 2
    assert location.geo_lat == pytest.approx(ATLANTA[0])
    assert location.geo_lng == pytest.approx(ATLANTA[1])
    assert location.state == "GA"
    assert location.country_code == "US"
    assert location.zipcode is None
    assert location.egrid_sub_region == "US"
