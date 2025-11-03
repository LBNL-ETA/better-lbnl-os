"""Building domain model."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from better_lbnl_os.models.utility_bills import UtilityBillData
from pydantic import BaseModel, Field, field_validator

from better_lbnl_os.constants import BuildingSpaceType, normalize_space_type


class BuildingData(BaseModel):
    """Domain model for building information with business logic methods."""

    name: str = Field(..., description="Building name")
    floor_area: float = Field(..., gt=0, description="Floor area in square feet")
    space_type: str = Field(..., description="Building space type category (display label)")
    location: str = Field(..., description="Building location")
    country_code: str = Field(default="US", description="Country code")
    climate_zone: str | None = Field(None, description="ASHRAE climate zone")

    @field_validator("space_type")
    @classmethod
    def validate_space_type(cls, v: str) -> str:
        """Normalize and validate the space type against known choices."""
        return normalize_space_type(v)

    def validate_bills(self, bills: list[UtilityBillData]) -> list[str]:
        """Validate utility bills for this building.

        Returns: list of validation error messages
        """
        errors = []
        if not bills:
            errors.append("No utility bills provided")
            return errors

        # Check for gaps in billing periods
        sorted_bills = sorted(bills, key=lambda b: b.start_date)
        for i in range(len(sorted_bills) - 1):
            gap_days = (sorted_bills[i + 1].start_date - sorted_bills[i].end_date).days
            if gap_days > 1:
                errors.append(
                    f"Gap of {gap_days} days between bills ending {sorted_bills[i].end_date} "
                    f"and starting {sorted_bills[i + 1].start_date}"
                )

        # Check for reasonable consumption values
        for bill in bills:
            daily_avg = bill.calculate_daily_average()
            if daily_avg <= 0:
                errors.append(f"Non-positive consumption for bill starting {bill.start_date}")
            elif daily_avg > 1000 * self.floor_area:  # Sanity check
                errors.append(f"Unusually high consumption for bill starting {bill.start_date}")

        return errors

    def get_benchmark_category(self) -> str:
        """Determine benchmark category based on space type."""
        from better_lbnl_os.constants import space_type_to_benchmark_category

        category = space_type_to_benchmark_category(self.space_type)
        return category.benchmark_id

    def get_space_type_code(self) -> str:
        """Return the enum code (name) for the current space type (e.g., "Office" -> "OFFICE")."""
        for st in BuildingSpaceType:
            if self.space_type == st.value:
                return st.name
        return "OTHER"


__all__ = ["BuildingData"]
