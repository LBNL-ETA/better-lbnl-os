"""Utility bill and calendarized data domain models."""

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from better_lbnl_os.constants import CONVERSION_TO_KWH
from better_lbnl_os.constants.energy import normalize_fuel_type, normalize_fuel_unit
from better_lbnl_os.models.weather import WeatherSeries


class UtilityBillData(BaseModel):
    """Domain model for utility bills with conversion methods."""

    fuel_type: str = Field(..., description="Type of fuel (ELECTRICITY, NATURAL_GAS, etc.)")
    start_date: date = Field(..., description="Billing period start date")
    end_date: date = Field(..., description="Billing period end date")
    consumption: float = Field(..., ge=0, description="Energy consumption")
    units: str = Field(..., description="Units of consumption")
    cost: float | None = Field(None, ge=0, description="Cost in dollars")

    @model_validator(mode="after")
    def validate_dates(self):
        """Validate that end date is after start date."""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self

    def get_days(self) -> int:
        """Calculate number of days in billing period."""
        return (self.end_date - self.start_date).days

    def to_kwh(self) -> float:
        """Convert consumption to kWh using standard conversion factors.

        Returns:
            Energy consumption in kWh
        """
        fuel = normalize_fuel_type(self.fuel_type)
        unit = normalize_fuel_unit(self.units)
        factor = CONVERSION_TO_KWH.get((fuel, unit), 1.0)
        return self.consumption * factor

    def calculate_daily_average(self) -> float:
        """Calculate average daily consumption.

        Returns:
            Average daily consumption in original units
        """
        days = self.get_days()
        return self.consumption / days if days > 0 else 0.0

    def calculate_cost_per_unit(self) -> float | None:
        """Calculate cost per unit of consumption.

        Returns:
            Cost per unit, or None if cost is not available
        """
        if self.cost is not None and self.consumption > 0:
            return self.cost / self.consumption
        return None


class TimeSeriesAggregation(BaseModel):
    months: list[date] = Field(default_factory=list)
    days_in_period: list[int] = Field(default_factory=list)
    energy_kwh: dict[str, list[float]] = Field(default_factory=dict)
    cost: dict[str, list[float]] = Field(default_factory=dict)
    ghg_kg: dict[str, list[float]] = Field(default_factory=dict)
    daily_eui_kwh_per_m2: dict[str, list[float]] = Field(default_factory=dict)
    unit_price_per_kwh: dict[str, list[float]] = Field(default_factory=dict)
    unit_emission_kg_per_kwh: dict[str, list[float]] = Field(default_factory=dict)


class EnergyAggregation(TimeSeriesAggregation):
    """Time series aggregation for total energy consumption."""

    pass


class FuelAggregation(TimeSeriesAggregation):
    """Time series aggregation broken down by fuel type."""

    pass


class CalendarizedData(BaseModel):
    """Calendarized energy data with weather and aggregations."""

    weather: WeatherSeries = Field(default_factory=WeatherSeries)
    aggregated: EnergyAggregation = Field(default_factory=EnergyAggregation)
    detailed: FuelAggregation = Field(default_factory=FuelAggregation)

    def to_legacy_dict(self) -> dict:
        """Convert to legacy dictionary format for backward compatibility.

        Returns:
            Dictionary in legacy format
        """

        def fmt_months(ms: list[date]) -> list[str]:
            return [m.strftime("%Y-%m-01") for m in ms]

        return {
            "weather": {
                "degC": list(self.weather.degC),
                "degF": list(self.weather.degF),
            },
            "detailed": {
                "v_x": fmt_months(self.detailed.months),
                "dict_v_energy": self.detailed.energy_kwh,
                "dict_v_costs": self.detailed.cost,
                "dict_v_ghg": self.detailed.ghg_kg,
                "dict_v_eui": self.detailed.daily_eui_kwh_per_m2,
                "dict_v_unit_prices": self.detailed.unit_price_per_kwh,
                "dict_v_ghg_factors": self.detailed.unit_emission_kg_per_kwh,
            },
            "aggregated": {
                "periods": fmt_months(self.aggregated.months),  # Modern key
                "v_x": fmt_months(self.aggregated.months),  # Legacy alias for Django compatibility
                "days_in_period": list(self.aggregated.days_in_period),  # Modern key
                "ls_n_days": list(
                    self.aggregated.days_in_period
                ),  # Legacy alias for Django compatibility
                "dict_v_energy": self.aggregated.energy_kwh,
                "dict_v_costs": self.aggregated.cost,
                "dict_v_ghg": self.aggregated.ghg_kg,
                "dict_v_eui": self.aggregated.daily_eui_kwh_per_m2,
                "dict_v_unit_prices": self.aggregated.unit_price_per_kwh,
                "dict_v_ghg_factors": self.aggregated.unit_emission_kg_per_kwh,
            },
        }

    @classmethod
    def from_legacy_dict(cls, data: dict) -> "CalendarizedData":
        """Create instance from legacy dictionary format.

        Args:
            data: Dictionary in legacy format

        Returns:
            CalendarizedData instance
        """

        def parse_months(vx: list[str] | None) -> list[date]:
            out: list[date] = []
            for s in vx or []:
                try:
                    # Accept YYYY-MM or YYYY-MM-01
                    if len(s) == 7:
                        dt = datetime.strptime(s + "-01", "%Y-%m-%d")
                    else:
                        dt = datetime.strptime(s, "%Y-%m-%d")
                    out.append(dt.date())
                except Exception:
                    continue
            return out

        weather_d = data.get("weather", {})
        detailed_d = data.get("detailed", {})
        aggregated_d = data.get("aggregated", {})

        weather = WeatherSeries(
            months=parse_months(detailed_d.get("v_x") or aggregated_d.get("v_x")),
            degC=list(weather_d.get("degC", [])),
            degF=list(weather_d.get("degF", [])),
        )

        detailed = FuelAggregation(
            months=parse_months(detailed_d.get("v_x")),
            days_in_period=list(
                aggregated_d.get("ls_n_days", [])
            ),  # No separate days at fuel-level
            energy_kwh=dict(detailed_d.get("dict_v_energy", {})),
            cost=dict(detailed_d.get("dict_v_costs", {})),
            ghg_kg=dict(detailed_d.get("dict_v_ghg", {})),
            daily_eui_kwh_per_m2=dict(detailed_d.get("dict_v_eui", {})),
            unit_price_per_kwh=dict(detailed_d.get("dict_v_unit_prices", {})),
            unit_emission_kg_per_kwh=dict(detailed_d.get("dict_v_ghg_factors", {})),
        )

        aggregated = EnergyAggregation(
            months=parse_months(aggregated_d.get("v_x")),
            days_in_period=list(aggregated_d.get("ls_n_days", [])),
            energy_kwh=dict(aggregated_d.get("dict_v_energy", {})),
            cost=dict(aggregated_d.get("dict_v_costs", {})),
            ghg_kg=dict(aggregated_d.get("dict_v_ghg", {})),
            daily_eui_kwh_per_m2=dict(aggregated_d.get("dict_v_eui", {})),
            unit_price_per_kwh=dict(aggregated_d.get("dict_v_unit_prices", {})),
            unit_emission_kg_per_kwh=dict(aggregated_d.get("dict_v_ghg_factors", {})),
        )

        return cls(weather=weather, detailed=detailed, aggregated=aggregated)


__all__ = [
    "CalendarizedData",
    "EnergyAggregation",
    "FuelAggregation",
    "UtilityBillData",
]
