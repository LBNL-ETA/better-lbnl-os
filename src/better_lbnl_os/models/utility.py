"""Utility bill domain model."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from better_lbnl_os.constants import CONVERSION_TO_KWH


class UtilityBillData(BaseModel):
    """Domain model for utility bills with conversion methods."""

    fuel_type: str = Field(..., description="Type of fuel (ELECTRICITY, NATURAL_GAS, etc.)")
    start_date: date = Field(..., description="Billing period start date")
    end_date: date = Field(..., description="Billing period end date")
    consumption: float = Field(..., ge=0, description="Energy consumption")
    units: str = Field(..., description="Units of consumption")
    cost: Optional[float] = Field(None, ge=0, description="Cost in dollars")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self

    def to_kwh(self) -> float:
        key = (self.fuel_type, self.units)
        factor = CONVERSION_TO_KWH.get(key, 1.0)
        return self.consumption * factor

    def get_days(self) -> int:
        return (self.end_date - self.start_date).days

    def calculate_daily_average(self) -> float:
        days = self.get_days()
        return self.consumption / days if days > 0 else 0.0

    def calculate_cost_per_unit(self) -> Optional[float]:
        if self.cost is not None and self.consumption > 0:
            return self.cost / self.consumption
        return None


__all__ = ["UtilityBillData"]
