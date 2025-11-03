"""Geocoding providers backed by Google Maps."""

from __future__ import annotations

import logging
from typing import Any

import geocoder

from better_lbnl_os.core.defaults import lookup_egrid_subregion, normalize_state_code
from better_lbnl_os.core.geocoding.interfaces import GeocodingProvider
from better_lbnl_os.models import LocationInfo

logger = logging.getLogger(__name__)


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
        result = self._call_geocoder(query)
        if result.postal is None and result.latlng:
            # Attempt reverse lookup to enrich postal/state metadata
            result = self._call_geocoder(tuple(result.latlng), reverse=True)
        return self._build_location_info(result)

    def reverse_geocode(self, latitude: float, longitude: float) -> LocationInfo:
        return self._build_location_info(self._call_geocoder((latitude, longitude), reverse=True))

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

    def _build_location_info(self, g) -> LocationInfo:
        lat, lng = g.latlng
        zipcode = getattr(g, "postal", None)
        country_raw = getattr(g, "country", None)
        country_code = self._normalize_country_code(country_raw)

        state_raw = getattr(g, "state", None)
        state = normalize_state_code(state_raw) if state_raw else None
        if state is None and state_raw:
            state = str(state_raw).strip().upper() or None
        if country_code != "US":
            state = state or None

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
