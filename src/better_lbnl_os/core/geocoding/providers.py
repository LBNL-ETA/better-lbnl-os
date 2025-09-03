"""Geocoding providers (Google Maps via geocoder library)."""

from __future__ import annotations

import logging
from typing import Optional

import geocoder

from better_lbnl_os.core.geocoding.interfaces import GeocodingProvider
from better_lbnl_os.models import LocationInfo


logger = logging.getLogger(__name__)


class GoogleMapsGeocodingProvider(GeocodingProvider):
    """Google Maps geocoding using the `geocoder` library (requires API key)."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google Maps API key is required")
        self.api_key = api_key

    def geocode(self, address: str) -> LocationInfo:
        if not isinstance(address, (str, int)) or not str(address).strip():
            raise ValueError("Invalid address; must be non-empty string or int")
        try:
            g = geocoder.google(str(address), key=self.api_key)
            # If postal is missing but latlng exists, try reverse to enrich components
            if g.postal is None and g.latlng:
                g = geocoder.google(g.latlng, method="reverse", key=self.api_key)
        except Exception as e:
            logger.exception("Google Maps geocoding failed")
            raise RuntimeError("Failed to call Google Maps Geocoding API via geocoder") from e

        if not g or g.latlng is None:
            raise ValueError("Geocoding returned no coordinates")

        lat, lng = g.latlng
        zipcode: Optional[str] = getattr(g, "postal", None)
        country_code: Optional[str] = getattr(g, "country", None)
        state: Optional[str] = getattr(g, "state", None)

        return LocationInfo(
            geo_lat=float(lat),
            geo_lng=float(lng),
            zipcode=zipcode,
            state=state or ("INT" if country_code and country_code != "US" else None),
            country_code=country_code or "INT",
            noaa_station_id=None,
            noaa_station_name=None,
            egrid_sub_region=country_code or "INT",
        )


class NominatimGeocodingProvider(GeocodingProvider):
    """OpenStreetMap Nominatim geocoding via `geocoder.osm` (no key).

    Notes:
    - Be courteous: provide a descriptive user agent string identifying your app.
    - Rate limits apply; this is suitable as a fallback or for light usage.
    """

    def __init__(self, user_agent: str = "better-lbnl-os/0.1 (geocoding)"):
        self.user_agent = user_agent

    def geocode(self, address: str) -> LocationInfo:
        if not isinstance(address, (str, int)) or not str(address).strip():
            raise ValueError("Invalid address; must be non-empty string or int")
        try:
            g = geocoder.osm(str(address), user_agent=self.user_agent)
        except Exception as e:
            logger.exception("OSM/Nominatim geocoding failed")
            raise RuntimeError("Failed to call Nominatim via geocoder") from e

        if not g or g.latlng is None:
            raise ValueError("Geocoding returned no coordinates")

        lat, lng = g.latlng
        zipcode: Optional[str] = getattr(g, "postal", None)
        country_code: Optional[str] = getattr(g, "country", None)
        state: Optional[str] = getattr(g, "state", None)

        return LocationInfo(
            geo_lat=float(lat),
            geo_lng=float(lng),
            zipcode=zipcode,
            state=state or ("INT" if country_code and country_code != "US" else None),
            country_code=country_code or "INT",
            noaa_station_id=None,
            noaa_station_name=None,
            egrid_sub_region=country_code or "INT",
        )
