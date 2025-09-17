"""Lean pipeline helpers to prepare and fit change-point models from calendarized data."""

from __future__ import annotations

import logging
from typing import TypedDict, Optional

import numpy as np

from better_lbnl_os.constants import DEFAULT_CVRMSE_THRESHOLD, DEFAULT_R2_THRESHOLD
from better_lbnl_os.core.changepoint import fit_changepoint_model
from better_lbnl_os.core.preprocessing import (
    calendarize_utility_bills,
    get_consecutive_months,
    trim_series,
)
from better_lbnl_os.models import ChangePointModelResult, UtilityBillData, WeatherData, CalendarizedData, LocationInfo
from better_lbnl_os.core.weather.service import WeatherService
from better_lbnl_os.core.weather.providers import OpenMeteoProvider
from better_lbnl_os.core.geocoding.providers import (
    GoogleMapsGeocodingProvider,
    NominatimGeocodingProvider,
)
from better_lbnl_os.core.geocoding.interfaces import GeocodingProvider

logger = logging.getLogger(__name__)


class ModelData(TypedDict):
    """Type definition for model-ready data."""
    temperature: list[float]
    eui: list[float]
    months: list[str]
    days: list[int]


def prepare_model_data(
    calendarized: dict | CalendarizedData,
    energy_types: tuple[str, ...] = ("ELECTRICITY", "FOSSIL_FUEL"),
    window: int = 12,
) -> dict[str, ModelData]:
    """Extract, gate, and trim model-ready arrays per energy type.

    Returns a dict keyed by energy type with keys: temperature, eui, months, days.
    Only includes energy types with sufficient consecutive data after trimming.
    """
    # Accept typed or legacy dict
    if hasattr(calendarized, "to_legacy_dict"):
        calendarized = calendarized.to_legacy_dict()  # type: ignore[assignment]

    out: dict[str, ModelData] = {}
    for et in energy_types:
        block = get_consecutive_months(calendarized, energy_type=et, window=window)
        if not block:
            continue
        eui_trim, degc_trim = trim_series(block["eui"], block["degC"])
        if len(eui_trim) < window or len(degc_trim) < window:
            logger.debug(f"Skipping {et}: insufficient data after trimming ({len(eui_trim)} months)")
            continue
        # Align months/days with trimmed indices
        # Find start index in original block
        # We can align by slicing from the first non-zero to last non-zero
        i0 = 0
        i1 = len(block["eui"])  # exclusive
        while i0 < i1 and float(block["eui"][i0]) == 0:
            i0 += 1
        while i1 > i0 and float(block["eui"][i1 - 1]) == 0:
            i1 -= 1
        months = block["months"][i0:i1]
        days = block["days"][i0:i1]

        out[et] = {
            "temperature": degc_trim,
            "eui": eui_trim,
            "months": months,
            "days": days,
        }
    return out


def resolve_location(
    *,
    address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    google_maps_api_key: Optional[str] = None,
    nominatim_user_agent: Optional[str] = None,
) -> LocationInfo:
    """Resolve a LocationInfo from coordinates or an address."""

    if latitude is not None and longitude is not None:
        return LocationInfo(
            geo_lat=float(latitude),
            geo_lng=float(longitude),
            zipcode=None,
            state=None,
            country_code="INT",
        )

    if not address:
        raise ValueError("Either coordinates or address must be provided for geocoding")

    if google_maps_api_key:
        provider: GeocodingProvider = GoogleMapsGeocodingProvider(api_key=google_maps_api_key)
    else:
        provider = NominatimGeocodingProvider(user_agent=nominatim_user_agent or "better-lbnl-os/0.1")

    return provider.geocode(address)


def fit_calendarized_models(
    calendarized: dict | CalendarizedData,
    min_r_squared: float = DEFAULT_R2_THRESHOLD,
    max_cv_rmse: float = DEFAULT_CVRMSE_THRESHOLD,
    energy_types: tuple[str, ...] = ("ELECTRICITY", "FOSSIL_FUEL"),
) -> dict[str, ChangePointModelResult]:
    """Fit change-point models for available energy types from calendarized data.
    
    Args:
        calendarized: Either a CalendarizedData object or legacy dict format
        min_r_squared: Minimum R² threshold for model acceptance
        max_cv_rmse: Maximum CV-RMSE threshold for model acceptance
        energy_types: Energy types to attempt fitting

    Returns:
        Dictionary mapping energy type to fitted model results
    """
    model_inputs = prepare_model_data(calendarized, energy_types=energy_types)
    results: dict[str, ChangePointModelResult] = {}
    for et, data in model_inputs.items():
        x = np.array(data["temperature"], dtype=float)
        y = np.array(data["eui"], dtype=float)

        # Check if we have temperature variation
        if len(np.unique(x)) < 2:
            logger.warning(f"Skipping {et}: insufficient temperature variation (likely missing weather data)")
            continue
        try:
            results[et] = fit_changepoint_model(x, y, min_r_squared=min_r_squared, max_cv_rmse=max_cv_rmse)
            logger.info(f"Successfully fit {results[et].model_type} model for {et} (R²={results[et].r_squared:.3f})")
        except Exception as e:
            logger.debug(f"Failed to fit model for {et}: {e}")
            continue
    return results


def fit_models_from_inputs(
    bills: list[UtilityBillData],
    floor_area: float,
    weather: list[WeatherData] | None,
    min_r_squared: float = DEFAULT_R2_THRESHOLD,
    max_cv_rmse: float = DEFAULT_CVRMSE_THRESHOLD,
) -> dict[str, ChangePointModelResult]:
    """Fit change-point models directly from raw utility bills and weather data.

    Args:
        bills: List of utility bills
        floor_area: Building floor area in square meters (must be positive)
        weather: Optional list of weather data
        min_r_squared: Minimum R² threshold for model acceptance
        max_cv_rmse: Maximum CV-RMSE threshold for model acceptance
        use_typed: If True, use typed CalendarizedData (recommended)

    Returns:
        Dictionary mapping energy type to fitted model results

    Raises:
        ValueError: If floor_area is not positive
    """
    if floor_area <= 0:
        raise ValueError(f"floor_area must be positive, got {floor_area}")

    calendarized = calendarize_utility_bills(bills=bills, floor_area=floor_area, weather=weather)
    return fit_calendarized_models(calendarized, min_r_squared=min_r_squared, max_cv_rmse=max_cv_rmse)


def get_weather_for_bills(
    bills: list[UtilityBillData],
    address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    google_maps_api_key: Optional[str] = None,
    nominatim_user_agent: Optional[str] = None,
    openmeteo_api_key: Optional[str] = None,
) -> list[WeatherData]:
    """Fetch monthly weather for the full bill date range using OpenMeteo.

    Args:
        bills: Utility bills to derive the date range
        address: Address string to geocode (if lat/lon not supplied)
        latitude, longitude: Direct coordinates (skip geocoding)
        google_maps_api_key: Optional Google Maps API key for geocoding
        nominatim_user_agent: Optional user agent for Nominatim geocoding fallback
        openmeteo_api_key: Optional OpenMeteo API key (paid archive)

    Returns:
        List of WeatherData, one per month.
    
    Raises:
        ValueError: If neither coordinates nor address provided, or if geocoding API key missing
    """
    if not bills:
        return []

    # Determine coordinates via geocoding if needed
    loc = resolve_location(
        address=address,
        latitude=latitude,
        longitude=longitude,
        google_maps_api_key=google_maps_api_key,
        nominatim_user_agent=nominatim_user_agent,
    )

    # Month range from bills
    min_start = min(b.start_date for b in bills)
    max_end = max(b.end_date for b in bills)
    start_year, start_month = min_start.year, min_start.month
    end_year, end_month = max_end.year, max_end.month

    service = WeatherService(provider=OpenMeteoProvider(api_key=openmeteo_api_key))
    return service.get_weather_range(
        location=loc,
        start_year=start_year,
        start_month=start_month,
        end_year=end_year,
        end_month=end_month,
    )


def fit_models_with_auto_weather(
    bills: list[UtilityBillData],
    floor_area: float,
    address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    google_maps_api_key: Optional[str] = None,
    nominatim_user_agent: Optional[str] = None,
    openmeteo_api_key: Optional[str] = None,
    min_r_squared: float = DEFAULT_R2_THRESHOLD,
    max_cv_rmse: float = DEFAULT_CVRMSE_THRESHOLD,
    use_typed: bool = True,
) -> dict[str, ChangePointModelResult]:
    """Convenience function that fetches weather and fits models in one call.
    
    Args:
        bills: List of utility bills
        floor_area: Building floor area in square meters (must be positive)
        address: Address string to geocode (if lat/lon not supplied)
        latitude, longitude: Direct coordinates (skip geocoding)
        google_maps_api_key: Optional Google Maps API key for geocoding
        nominatim_user_agent: Optional user agent for Nominatim geocoding fallback
        openmeteo_api_key: Optional OpenMeteo API key (paid archive)
        min_r_squared: Minimum R² threshold for model acceptance
        max_cv_rmse: Maximum CV-RMSE threshold for model acceptance
        use_typed: If True, use typed CalendarizedData (recommended)
    
    Returns:
        Dictionary mapping energy type to fitted model results
    """
    weather = get_weather_for_bills(
        bills=bills,
        address=address,
        latitude=latitude,
        longitude=longitude,
        google_maps_api_key=google_maps_api_key,
        nominatim_user_agent=nominatim_user_agent,
        openmeteo_api_key=openmeteo_api_key,
    )
    
    return fit_models_from_inputs(
        bills=bills,
        floor_area=floor_area,
        weather=weather,
        min_r_squared=min_r_squared,
        max_cv_rmse=max_cv_rmse,
        use_typed=use_typed,
    )
