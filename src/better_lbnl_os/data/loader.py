"""Flexible loader for reference benchmark statistics."""

import importlib.resources
import json
from pathlib import Path

from better_lbnl_os.constants.building_types import BuildingSpaceType
from better_lbnl_os.models.benchmarking import BenchmarkStatistics

from .reference_data_models import ReferenceDataManifest


class ReferenceStatisticsLoader:
    """Loader for reference benchmark statistics with flexible data sources."""

    def __init__(self, custom_path: str | None = None):
        """Initialize loader with optional custom data path.

        Args:
            custom_path: Path to custom JSON manifest. If None, uses built-in data.
        """
        self.custom_path = custom_path
        self.data_source = custom_path or "built-in"
        self._manifest: ReferenceDataManifest | None = None
        self._cache: dict[tuple[str, BuildingSpaceType], BenchmarkStatistics] = {}

    def _load_manifest(self) -> ReferenceDataManifest:
        """Load manifest from either custom path or built-in data."""
        if self._manifest is not None:
            return self._manifest

        if self.custom_path:
            # Load from custom file path
            custom_file = Path(self.custom_path)
            if not custom_file.exists():
                raise FileNotFoundError(f"Custom reference data file not found: {self.custom_path}")

            with open(custom_file, encoding="utf-8") as f:
                manifest_data = json.load(f)
        else:
            # Load from built-in package data
            try:
                with importlib.resources.open_text(
                    "better_lbnl_os.data.defaults", "manifest.json"
                ) as f:
                    manifest_data = json.load(f)
            except (FileNotFoundError, ImportError):
                manifest_data = {}

        if "entries" not in manifest_data:
            ref_meta = manifest_data.get("reference_statistics")
            if ref_meta and isinstance(ref_meta, dict):
                ref_file = ref_meta.get("file", "reference_statistics.json")
                try:
                    with importlib.resources.open_text(
                        "better_lbnl_os.data.defaults", ref_file
                    ) as ref_fp:
                        manifest_data = json.load(ref_fp)
                except FileNotFoundError:
                    manifest_data = {"version": "1.0.0", "created": None, "entries": []}
            else:
                manifest_data = {"version": "1.0.0", "created": None, "entries": []}

        # Convert benchmark_id format to BuildingSpaceType enums
        processed_data = manifest_data.copy()
        for entry in processed_data.get("entries", []):
            if "building_type" in entry and isinstance(entry["building_type"], str):
                try:
                    # Convert from benchmark_id to enum
                    entry["building_type"] = BuildingSpaceType.from_benchmark_id(
                        entry["building_type"]
                    )
                except ValueError:
                    # If conversion fails, skip this entry
                    continue

        self._manifest = ReferenceDataManifest(**processed_data)
        return self._manifest

    def get_statistics(
        self, country_code: str, building_type: BuildingSpaceType
    ) -> BenchmarkStatistics | None:
        """Load statistics for given country and building type.

        Args:
            country_code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'MX')
            building_type: Building type category

        Returns:
            BenchmarkStatistics if available, None otherwise
        """
        cache_key = (country_code, building_type)

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Load from manifest
        manifest = self._load_manifest()
        entry = manifest.find_entry(country_code, building_type)

        if entry is None:
            return None

        # Cache and return
        self._cache[cache_key] = entry.statistics
        return entry.statistics

    def list_available(self) -> list[tuple[str, BuildingSpaceType]]:
        """List all available (country_code, building_type) combinations.

        Returns:
            List of tuples containing (country_code, building_type)
        """
        manifest = self._load_manifest()
        return manifest.list_available()

    def has_statistics(self, country_code: str, building_type: BuildingSpaceType) -> bool:
        """Check if statistics are available for given country and building type.

        Args:
            country_code: ISO 3166-1 alpha-2 country code
            building_type: Building type category

        Returns:
            True if statistics are available, False otherwise
        """
        return self.get_statistics(country_code, building_type) is not None

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()

    def reload(self) -> None:
        """Reload manifest and clear cache."""
        self._manifest = None
        self.clear_cache()
