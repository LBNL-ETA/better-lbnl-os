"""Domain models with data and business logic for building energy analytics."""

from datetime import date
from typing import List, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator


class LocationInfo(BaseModel):
    """Domain model for geocoded location information."""
    
    geo_lat: float = Field(..., description="Latitude coordinate")
    geo_lng: float = Field(..., description="Longitude coordinate") 
    zipcode: Optional[str] = Field(None, description="Postal/ZIP code")
    state: Optional[str] = Field(None, description="State or province")
    country_code: str = Field(default="US", description="ISO country code")
    noaa_station_id: Optional[str] = Field(None, description="NOAA weather station ID")
    noaa_station_name: Optional[str] = Field(None, description="NOAA weather station name")
    egrid_sub_region: Optional[str] = Field(None, description="eGrid subregion for emissions")
    
    def is_valid_coordinates(self) -> bool:
        """Check if coordinates are within valid ranges.
        
        Returns:
            True if coordinates are valid
        """
        return (-90 <= self.geo_lat <= 90) and (-180 <= self.geo_lng <= 180)
    
    def calculate_distance_to(self, other: "LocationInfo") -> float:
        """Calculate distance to another location using haversine formula.
        
        Args:
            other: Another LocationInfo object
            
        Returns:
            Distance in kilometers
        """
        from better_lbnl.utils.geography import haversine_distance
        return haversine_distance(
            self.geo_lat, self.geo_lng, 
            other.geo_lat, other.geo_lng
        )


class BuildingData(BaseModel):
    """Domain model for building information with business logic methods."""

    name: str = Field(..., description="Building name")
    floor_area: float = Field(..., gt=0, description="Floor area in square feet")
    space_type: str = Field(..., description="Building space type category")
    location: str = Field(..., description="Building location")
    country_code: str = Field(default="US", description="Country code")
    climate_zone: Optional[str] = Field(None, description="ASHRAE climate zone")

    @field_validator("space_type")
    @classmethod
    def validate_space_type(cls, v):
        """Validate space type is in allowed categories."""
        allowed_types = [
            "Office",
            "Retail",
            "School",
            "Hospital",
            "Hotel",
            "Warehouse",
            "Restaurant",
            "Laboratory",
            "Data Center",
            "Other",
        ]
        if v not in allowed_types:
            raise ValueError(f"Space type must be one of {allowed_types}")
        return v

    def calculate_eui(self, annual_energy_kwh: float) -> float:
        """Calculate Energy Use Intensity (kBtu/sqft/year).
        
        Args:
            annual_energy_kwh: Annual energy consumption in kWh
            
        Returns:
            EUI in kBtu/sqft/year
        """
        kbtu_per_kwh = 3.412
        return (annual_energy_kwh * kbtu_per_kwh) / self.floor_area

    def calculate_monthly_eui(self, bills: List["UtilityBillData"]) -> np.ndarray:
        """Calculate monthly EUI from utility bills.
        
        Args:
            bills: List of utility bill data
            
        Returns:
            Array of monthly EUI values
        """
        monthly_eui = []
        for bill in bills:
            kwh = bill.to_kwh()
            days = bill.get_days()
            daily_kwh = kwh / days if days > 0 else 0
            monthly_kwh = daily_kwh * 30  # Normalize to 30-day month
            eui = self.calculate_eui(monthly_kwh * 12)  # Annualize for EUI
            monthly_eui.append(eui)
        return np.array(monthly_eui)

    def validate_bills(self, bills: List["UtilityBillData"]) -> List[str]:
        """Validate utility bills for this building.
        
        Args:
            bills: List of utility bill data
            
        Returns:
            List of validation error messages
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
        """Determine benchmark category based on space type.
        
        Returns:
            Benchmark category string
        """
        category_map = {
            "Office": "COMMERCIAL_OFFICE",
            "Retail": "COMMERCIAL_RETAIL",
            "School": "EDUCATION_K12",
            "Hospital": "HEALTHCARE_HOSPITAL",
            "Hotel": "LODGING_HOTEL",
            "Warehouse": "WAREHOUSE_UNREFRIGERATED",
            "Restaurant": "FOOD_SERVICE_RESTAURANT",
            "Laboratory": "LABORATORY",
            "Data Center": "DATA_CENTER",
            "Other": "OTHER",
        }
        return category_map.get(self.space_type, "OTHER")


class UtilityBillData(BaseModel):
    """Domain model for utility bills with conversion methods."""

    fuel_type: str = Field(..., description="Type of fuel (ELECTRICITY, NATURAL_GAS, etc.)")
    start_date: date = Field(..., description="Billing period start date")
    end_date: date = Field(..., description="Billing period end date")
    consumption: float = Field(..., ge=0, description="Energy consumption")
    units: str = Field(..., description="Units of consumption")
    cost: Optional[float] = Field(None, ge=0, description="Cost in dollars")

    @model_validator(mode='after')
    def validate_dates(self):
        """Validate end date is after start date."""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self

    def to_kwh(self) -> float:
        """Convert consumption to kWh using standard conversion factors.
        
        Returns:
            Consumption in kWh
        """
        conversion_factors = {
            ("ELECTRICITY", "kWh"): 1.0,
            ("ELECTRICITY", "MWh"): 1000.0,
            ("NATURAL_GAS", "therms"): 29.3,
            ("NATURAL_GAS", "ccf"): 29.3,
            ("NATURAL_GAS", "mcf"): 293.0,
            ("NATURAL_GAS", "MMBtu"): 293.0,
            ("FUEL_OIL", "gallons"): 40.6,
            ("PROPANE", "gallons"): 27.0,
            ("STEAM", "MLbs"): 293.0,
            ("STEAM", "therms"): 29.3,
        }
        key = (self.fuel_type, self.units)
        factor = conversion_factors.get(key, 1.0)
        return self.consumption * factor

    def get_days(self) -> int:
        """Calculate number of days in billing period.
        
        Returns:
            Number of days
        """
        return (self.end_date - self.start_date).days

    def calculate_daily_average(self) -> float:
        """Calculate average daily consumption.
        
        Returns:
            Average daily consumption in original units
        """
        days = self.get_days()
        return self.consumption / days if days > 0 else 0.0

    def calculate_cost_per_unit(self) -> Optional[float]:
        """Calculate cost per unit of energy.
        
        Returns:
            Cost per unit or None if cost not available
        """
        if self.cost is not None and self.consumption > 0:
            return self.cost / self.consumption
        return None


class WeatherData(BaseModel):
    """Domain model for weather data with calculation methods."""

    station_id: Optional[str] = Field(None, description="Weather station identifier")
    latitude: float = Field(..., description="Station latitude")
    longitude: float = Field(..., description="Station longitude")
    year: int = Field(..., description="Year of observation")
    month: int = Field(..., ge=1, le=12, description="Month of observation")
    avg_temp_c: float = Field(..., description="Monthly average temperature in Celsius")
    min_temp_c: Optional[float] = Field(None, description="Minimum temperature in Celsius")
    max_temp_c: Optional[float] = Field(None, description="Maximum temperature in Celsius")
    data_source: str = Field(default="OpenMeteo", description="Data source (NOAA, OpenMeteo, etc.)")
    daily_temps_c: Optional[List[float]] = Field(None, description="Daily temperatures for the month")

    @property
    def avg_temp_f(self) -> float:
        """Average temperature in Fahrenheit."""
        from better_lbnl.core.weather.calculations import celsius_to_fahrenheit
        return celsius_to_fahrenheit(self.avg_temp_c)
    
    @property
    def min_temp_f(self) -> Optional[float]:
        """Minimum temperature in Fahrenheit."""
        if self.min_temp_c is not None:
            from better_lbnl.core.weather.calculations import celsius_to_fahrenheit
            return celsius_to_fahrenheit(self.min_temp_c)
        return None
    
    @property
    def max_temp_f(self) -> Optional[float]:
        """Maximum temperature in Fahrenheit."""
        if self.max_temp_c is not None:
            from better_lbnl.core.weather.calculations import celsius_to_fahrenheit
            return celsius_to_fahrenheit(self.max_temp_c)
        return None

    def calculate_hdd(self, base_temp_f: float = 65.0, use_daily: bool = True) -> float:
        """Calculate Heating Degree Days.
        
        Args:
            base_temp_f: Base temperature in Fahrenheit (default 65°F)
            use_daily: Use daily temps if available, else use monthly average
            
        Returns:
            HDD value
        """
        from better_lbnl.core.weather.calculations import (
            calculate_heating_degree_days, 
            estimate_monthly_hdd,
            convert_temperature_list
        )
        
        if use_daily and self.daily_temps_c:
            # Convert daily temps to Fahrenheit and calculate HDD
            daily_temps_f = convert_temperature_list(self.daily_temps_c, 'C', 'F')
            return calculate_heating_degree_days(daily_temps_f, base_temp_f, 'F')
        else:
            # Use monthly average for estimation
            import calendar
            days_in_month = calendar.monthrange(self.year, self.month)[1]
            return estimate_monthly_hdd(self.avg_temp_f, days_in_month, base_temp_f)

    def calculate_cdd(self, base_temp_f: float = 65.0, use_daily: bool = True) -> float:
        """Calculate Cooling Degree Days.
        
        Args:
            base_temp_f: Base temperature in Fahrenheit (default 65°F)
            use_daily: Use daily temps if available, else use monthly average
            
        Returns:
            CDD value
        """
        from better_lbnl.core.weather.calculations import (
            calculate_cooling_degree_days,
            estimate_monthly_cdd,
            convert_temperature_list
        )
        
        if use_daily and self.daily_temps_c:
            # Convert daily temps to Fahrenheit and calculate CDD
            daily_temps_f = convert_temperature_list(self.daily_temps_c, 'C', 'F')
            return calculate_cooling_degree_days(daily_temps_f, base_temp_f, 'F')
        else:
            # Use monthly average for estimation
            import calendar
            days_in_month = calendar.monthrange(self.year, self.month)[1]
            return estimate_monthly_cdd(self.avg_temp_f, days_in_month, base_temp_f)
    
    def is_valid_temperature(self) -> bool:
        """Validate temperature is within reasonable range."""
        from better_lbnl.core.weather.calculations import validate_temperature_range
        return validate_temperature_range(self.avg_temp_c)


class WeatherStation(BaseModel):
    """Domain model for weather station information."""
    
    station_id: str = Field(..., description="Station identifier (e.g., NOAA ID)")
    name: str = Field(..., description="Station name")
    latitude: float = Field(..., ge=-90, le=90, description="Station latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Station longitude")
    elevation: Optional[float] = Field(None, description="Station elevation in meters")
    distance_km: Optional[float] = Field(None, description="Distance from target location in km")
    data_source: str = Field(default="NOAA", description="Data source")
    
    def distance_to(self, lat: float, lng: float) -> float:
        """Calculate distance to a location using haversine formula.
        
        Args:
            lat: Target latitude
            lng: Target longitude
            
        Returns:
            Distance in kilometers
        """
        from better_lbnl.utils.geography import haversine_distance
        return haversine_distance(self.latitude, self.longitude, lat, lng)


class ChangePointModelResult(BaseModel):
    """Domain model for change-point model results with validation methods."""

    heating_slope: Optional[float] = Field(None, description="Heating slope coefficient")
    heating_change_point: Optional[float] = Field(None, description="Heating change point temperature")
    baseload: float = Field(..., description="Baseload consumption")
    cooling_change_point: Optional[float] = Field(None, description="Cooling change point temperature")
    cooling_slope: Optional[float] = Field(None, description="Cooling slope coefficient")
    r_squared: float = Field(..., ge=0, le=1, description="R-squared value")
    cvrmse: float = Field(..., ge=0, description="CV(RMSE) value")
    model_type: str = Field(..., description="Model type (1P, 3P-H, 3P-C, 5P)")
    heating_pvalue: Optional[float] = Field(None, description="P-value for heating slope significance")
    cooling_pvalue: Optional[float] = Field(None, description="P-value for cooling slope significance")

    def is_valid(self, min_r_squared: float = 0.6, max_cvrmse: float = 0.5) -> bool:
        """Check if model meets quality thresholds.
        
        Args:
            min_r_squared: Minimum acceptable R-squared value
            max_cvrmse: Maximum acceptable CV(RMSE) value
            
        Returns:
            True if model meets quality thresholds
        """
        return self.r_squared >= min_r_squared and self.cvrmse <= max_cvrmse

    def get_model_complexity(self) -> int:
        """Get number of parameters in the model.
        
        Returns:
            Number of parameters (1, 3, or 5)
        """
        model_params = {"1P": 1, "3P-H": 3, "3P-C": 3, "5P": 5}
        return model_params.get(self.model_type, 1)

    def estimate_annual_consumption(self, annual_hdd: float, annual_cdd: float) -> float:
        """Estimate annual energy consumption from degree days.
        
        Args:
            annual_hdd: Annual heating degree days
            annual_cdd: Annual cooling degree days
            
        Returns:
            Estimated annual consumption
        """
        annual = self.baseload * 365
        if self.heating_slope:
            annual += self.heating_slope * annual_hdd
        if self.cooling_slope:
            annual += self.cooling_slope * annual_cdd
        return annual


class BenchmarkResult(BaseModel):
    """Domain model for benchmark results with rating methods."""

    building_id: str = Field(..., description="Building identifier")
    percentile: float = Field(..., ge=0, le=100, description="Percentile ranking")
    z_score: float = Field(..., description="Statistical z-score")
    rating: str = Field(..., description="Performance rating")
    target_eui: float = Field(..., gt=0, description="Target EUI for improvement")
    median_eui: float = Field(..., gt=0, description="Median EUI for peer group")

    def get_rating_color(self) -> str:
        """Get color code for performance rating.
        
        Returns:
            Color code string
        """
        color_map = {
            "Excellent": "green",
            "Good": "lightgreen",
            "Average": "yellow",
            "Below Average": "orange",
            "Poor": "red",
        }
        return color_map.get(self.rating, "gray")

    def calculate_savings_potential(self, current_eui: float) -> float:
        """Calculate potential savings from reaching target.
        
        Args:
            current_eui: Current building EUI
            
        Returns:
            Potential savings percentage
        """
        if current_eui > 0:
            return max(0, (current_eui - self.target_eui) / current_eui * 100)
        return 0.0


class SavingsEstimate(BaseModel):
    """Domain model for savings estimates with calculation methods."""

    energy_savings_kwh: float = Field(..., description="Annual energy savings in kWh")
    cost_savings_usd: float = Field(..., description="Annual cost savings in USD")
    emissions_savings_kg_co2: float = Field(..., description="Annual emissions savings in kg CO2")
    percent_reduction: float = Field(..., ge=0, le=100, description="Percentage reduction")

    def calculate_roi(self, investment_cost: float, discount_rate: float = 0.05) -> float:
        """Calculate simple return on investment.
        
        Args:
            investment_cost: Initial investment cost in USD
            discount_rate: Annual discount rate
            
        Returns:
            ROI percentage
        """
        if investment_cost > 0:
            return (self.cost_savings_usd / investment_cost) * 100
        return 0.0

    def calculate_payback_period(self, investment_cost: float) -> float:
        """Calculate simple payback period.
        
        Args:
            investment_cost: Initial investment cost in USD
            
        Returns:
            Payback period in years
        """
        if self.cost_savings_usd > 0:
            return investment_cost / self.cost_savings_usd
        return float("inf")


class EEMeasureRecommendation(BaseModel):
    """Domain model for energy efficiency measure recommendations."""

    measure_id: str = Field(..., description="Unique measure identifier")
    name: str = Field(..., description="Measure name")
    category: str = Field(..., description="Measure category")
    description: str = Field(..., description="Detailed description")
    estimated_savings: SavingsEstimate = Field(..., description="Estimated savings")
    confidence_level: str = Field(..., description="Confidence level (High/Medium/Low)")
    implementation_difficulty: str = Field(..., description="Implementation difficulty")

    def is_applicable(self, building: BuildingData) -> bool:
        """Check if measure is applicable to a building.
        
        Args:
            building: Building data
            
        Returns:
            True if measure is applicable
        """
        # Placeholder logic - would be expanded with real rules
        return True

    def prioritize_score(self) -> float:
        """Calculate prioritization score for the measure.
        
        Returns:
            Priority score (0-100)
        """
        # Simple scoring based on savings and difficulty
        savings_score = min(self.estimated_savings.percent_reduction * 2, 50)
        
        difficulty_scores = {"Easy": 50, "Medium": 30, "Hard": 10}
        difficulty_score = difficulty_scores.get(self.implementation_difficulty, 20)
        
        confidence_multipliers = {"High": 1.0, "Medium": 0.8, "Low": 0.6}
        confidence_mult = confidence_multipliers.get(self.confidence_level, 0.7)
        
        return (savings_score + difficulty_score) * confidence_mult