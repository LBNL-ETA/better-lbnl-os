"""Geocoding provider interface for pluggable implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from better_lbnl_os.models import LocationInfo


class GeocodingProvider(ABC):
    """Abstract geocoding provider."""

    @abstractmethod
    def geocode(self, address: str) -> LocationInfo:
        """Return a LocationInfo for the given address string."""
        raise NotImplementedError

    def get_provider_name(self) -> str:
        return self.__class__.__name__
