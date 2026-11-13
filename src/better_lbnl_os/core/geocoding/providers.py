"""Geocoding providers backed by Google Maps."""

from __future__ import annotations

import logging
from typing import Any

import geocoder

from better_lbnl_os.core.defaults import lookup_egrid_subregion, normalize_state_code
from better_lbnl_os.core.geocoding.interfaces import GeocodingProvider
from better_lbnl_os.models import LocationInfo
from better_lbnl_os.utils.geography import haversine_distance

logger = logging.getLogger(__name__)

# Reverse geocoding only fills a missing postal code. Google's first reverse
# hit is not guaranteed to be the forward place (it has returned an unrelated
# country), so require the same country, normalized state, and a nearby point.
_REVERSE_POSTAL_MATCH_KM = 25.0
_MISSING = object()


class GoogleMapsGeocodingProvider(GeocodingProvider):
    """Google Maps geocoding using the `geocoder` library (API key required)."""

    def __init__(self, api_key: str):
        if not api_key or not str(api_key).strip():
            raise ValueError("Google Maps API key is required")
        self.api_key = api_key

    def geocode(self, address: str) -> LocationInfo:
        if not isinstance(address, (str, int)) or not str(address).strip():
            raise ValueError("Invalid address; must be non-empty string or int")
        query = str(address).strip()
        forward = self._call_geocoder(query)
        zipcode = getattr(forward, "postal", None)
        if zipcode is None and forward.latlng:
            # Keep the forward place. Reverse results only supply a ZIP code.
            zipcode = self._postal_from_reverse(forward)
        return self._build_location_info(forward, zipcode=zipcode)

    def reverse_geocode(self, latitude: float, longitude: float) -> LocationInfo:
        return self._build_location_info(self._call_geocoder((latitude, longitude), reverse=True))

    def _postal_from_reverse(self, forward: Any) -> str | None:
        """Return a postal code from the first reverse hit that is the same place."""
        reverse = self._call_geocoder(tuple(forward.latlng), reverse=True)
        country = self._normalize_country_code(getattr(forward, "country", None))
        state = self._normalized_state(getattr(forward, "state", None))
        latitude, longitude = forward.latlng

        for candidate in reverse:
            postal = self._postal_text(getattr(candidate, "postal", None))
            if postal is None:
                continue
            if self._reverse_hit_matches(candidate, country, state, latitude, longitude):
                return postal
        return None

    def _reverse_hit_matches(
        self,
        candidate: Any,
        country: str,
        state: str | None,
        latitude: float,
        longitude: float,
    ) -> bool:
        """True when a reverse hit agrees with the forward country, state, and point."""
        candidate_country = self._normalize_country_code(getattr(candidate, "country", None))
        if candidate_country != country:
            return False
        if self._normalized_state(getattr(candidate, "state", None)) != state:
            return False
        latlng = getattr(candidate, "latlng", None)
        if not latlng or len(latlng) < 2:
            return False
        distance_km = haversine_distance(
            float(latitude), float(longitude), float(latlng[0]), float(latlng[1])
        )
        return distance_km <= _REVERSE_POSTAL_MATCH_KM

    def _call_geocoder(self, query: Any, *, reverse: bool = False):
        try:
            if reverse:
                g = geocoder.google(query, method="reverse", key=self.api_key)
            else:
                g = geocoder.google(query, key=self.api_key)
        except Exception as exc:  # pragma: no cover - network failure
            logger.exception("Google Maps geocoding request failed")
            raise RuntimeError("Failed to call Google Maps Geocoding API via geocoder") from exc

        if not g or g.latlng is None:
            raise ValueError("Geocoding returned no coordinates")

        error = getattr(g, "error", None)
        if error == "REQUEST_DENIED":
            raise PermissionError("Google Maps API denied geocoding request")

        return g

    def _build_location_info(self, g, *, zipcode: Any = _MISSING) -> LocationInfo:
        lat, lng = g.latlng
        if zipcode is _MISSING:
            zipcode = getattr(g, "postal", None)
        country_raw = getattr(g, "country", None)
        country_code = self._normalize_country_code(country_raw)
        state = self._normalized_state(getattr(g, "state", None))

        egrid_sub_region = None
        if country_code == "US" and zipcode:
            egrid_sub_region = lookup_egrid_subregion(zipcode)
        if not egrid_sub_region:
            egrid_sub_region = country_code

        return LocationInfo(
            geo_lat=float(lat),
            geo_lng=float(lng),
            zipcode=zipcode,
            state=state,
            country_code=country_code,
            noaa_station_id=None,
            noaa_station_name=None,
            egrid_sub_region=egrid_sub_region,
        )

    @staticmethod
    def _normalized_state(state_raw: Any) -> str | None:
        """Return a comparable state key, using the USPS abbreviation when known."""
        if not state_raw:
            return None
        state = normalize_state_code(state_raw)
        if state is None:
            text = str(state_raw).strip().upper()
            return text or None
        return state

    @staticmethod
    def _postal_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _normalize_country_code(value: Any) -> str:
        if not value:
            return "INT"
        code = str(value).strip().upper()
        if not code:
            return "INT"
        if code in {"UNITED STATES", "UNITED STATES OF AMERICA", "USA"}:
            return "US"
        if len(code) > 2 and " " in code:
            return code.split()[0]
        return code
