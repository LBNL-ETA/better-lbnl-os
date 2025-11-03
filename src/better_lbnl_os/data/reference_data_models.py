"""Data models for reference benchmark statistics."""

from pydantic import BaseModel, Field

from better_lbnl_os.constants.building_types import BuildingSpaceType
from better_lbnl_os.models.benchmarking import BenchmarkStatistics


class ReferenceDataEntry(BaseModel):
    """Single entry in reference statistics database."""

    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    building_type: BuildingSpaceType = Field(..., description="Building type category")
    statistics: BenchmarkStatistics = Field(..., description="Benchmark statistics for this entry")
    metadata: dict | None = Field(
        default=None, description="Additional metadata (source, sample size, etc.)"
    )


class ReferenceDataManifest(BaseModel):
    """Manifest describing available reference statistics."""

    version: str = Field(..., description="Version of the reference data")
    created: str | None = Field(default=None, description="Creation date")
    entries: list[ReferenceDataEntry] = Field(..., description="List of reference data entries")

    def find_entry(
        self, country_code: str, building_type: BuildingSpaceType
    ) -> ReferenceDataEntry | None:
        """Find entry by country and building type."""
        for entry in self.entries:
            if entry.country_code == country_code and entry.building_type == building_type:
                return entry
        return None

    def list_available(self) -> list[tuple[str, BuildingSpaceType]]:
        """List all available (country_code, building_type) combinations."""
        return [(entry.country_code, entry.building_type) for entry in self.entries]
