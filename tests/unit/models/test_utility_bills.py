"""Unit tests for UtilityBillData domain model."""

from datetime import date

import pytest

from better_lbnl_os.models import UtilityBillData


class TestUtilityBillData:
    """Test UtilityBillData domain model."""

    def test_bill_creation(self):
        """Test creating a UtilityBillData instance."""
        bill = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=1000,
            units="kWh",
            cost=150.0,
        )

        assert bill.fuel_type == "ELECTRICITY"
        assert bill.consumption == 1000
        assert bill.cost == 150.0

    def test_to_kwh_conversion(self):
        """Test energy unit conversion to kWh."""
        # Test electricity (no conversion)
        bill_elec = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=1000,
            units="kWh",
        )
        assert bill_elec.to_kwh() == 1000

        # Test natural gas conversion (therms to kWh)
        bill_gas = UtilityBillData(
            fuel_type="NATURAL_GAS",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=100,
            units="therms",
        )
        assert abs(bill_gas.to_kwh() - 2930.7) < 0.1  # 100 therms * 29.307 kWh/therm

    def test_get_days(self):
        """Test billing period day calculation."""
        bill = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=1000,
            units="kWh",
        )

        assert bill.get_days() == 30

    def test_invalid_dates(self):
        """Test date validation."""
        with pytest.raises(ValueError, match="End date must be after start date"):
            UtilityBillData(
                fuel_type="ELECTRICITY",
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1),
                consumption=1000,
                units="kWh",
            )

    def test_calculate_cost_per_unit_with_cost(self):
        """Test cost per unit calculation when cost is provided."""
        bill = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=1000,
            units="kWh",
            cost=150.0,
        )

        cost_per_unit = bill.calculate_cost_per_unit()
        assert cost_per_unit is not None
        assert abs(cost_per_unit - 0.15) < 0.001  # $150 / 1000 kWh = $0.15/kWh

    def test_calculate_cost_per_unit_no_cost(self):
        """Test cost per unit returns None when cost is not provided."""
        bill = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=1000,
            units="kWh",
        )

        assert bill.calculate_cost_per_unit() is None

    def test_calculate_cost_per_unit_zero_consumption(self):
        """Test cost per unit returns None when consumption is zero."""
        bill = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=0,
            units="kWh",
            cost=150.0,
        )

        assert bill.calculate_cost_per_unit() is None

    def test_calculate_daily_average(self):
        """Test daily average consumption calculation."""
        bill = UtilityBillData(
            fuel_type="ELECTRICITY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            consumption=900,
            units="kWh",
        )

        daily_avg = bill.calculate_daily_average()
        assert abs(daily_avg - 30.0) < 0.1  # 900 kWh / 30 days = 30 kWh/day


class TestCalendarizedData:
    """Test CalendarizedData and related aggregation models."""

    def test_calendarized_data_creation(self):
        """Test creating CalendarizedData with defaults."""
        from better_lbnl_os.models.utility_bills import CalendarizedData

        data = CalendarizedData()
        assert data.weather is not None
        assert data.aggregated is not None
        assert data.detailed is not None

    def test_to_legacy_dict(self):
        """Test converting CalendarizedData to legacy dictionary format."""
        from better_lbnl_os.models.utility_bills import (
            CalendarizedData,
            EnergyAggregation,
            FuelAggregation,
        )
        from better_lbnl_os.models.weather import WeatherSeries

        # Create CalendarizedData with sample data
        months = [date(2024, 1, 1), date(2024, 2, 1)]
        weather = WeatherSeries(months=months, degC=[15.0, 16.0], degF=[59.0, 60.8])
        aggregated = EnergyAggregation(
            months=months,
            days_in_period=[31, 29],
            energy_kwh={"ELECTRICITY": [1000.0, 1100.0]},
            cost={"ELECTRICITY": [150.0, 165.0]},
            ghg_kg={"ELECTRICITY": [500.0, 550.0]},
            daily_eui_kwh_per_m2={"ELECTRICITY": [0.5, 0.55]},
            unit_price_per_kwh={"ELECTRICITY": [0.15, 0.15]},
            unit_emission_kg_per_kwh={"ELECTRICITY": [0.5, 0.5]},
        )
        detailed = FuelAggregation(
            months=months,
            days_in_period=[31, 29],
            energy_kwh={"ELECTRICITY": [1000.0, 1100.0]},
            cost={"ELECTRICITY": [150.0, 165.0]},
            ghg_kg={"ELECTRICITY": [500.0, 550.0]},
            daily_eui_kwh_per_m2={"ELECTRICITY": [0.5, 0.55]},
            unit_price_per_kwh={"ELECTRICITY": [0.15, 0.15]},
            unit_emission_kg_per_kwh={"ELECTRICITY": [0.5, 0.5]},
        )

        data = CalendarizedData(weather=weather, aggregated=aggregated, detailed=detailed)
        legacy_dict = data.to_legacy_dict()

        # Check weather data
        assert "weather" in legacy_dict
        assert legacy_dict["weather"]["degC"] == [15.0, 16.0]
        assert legacy_dict["weather"]["degF"] == [59.0, 60.8]

        # Check aggregated data
        assert "aggregated" in legacy_dict
        assert legacy_dict["aggregated"]["periods"] == ["2024-01-01", "2024-02-01"]
        assert legacy_dict["aggregated"]["v_x"] == ["2024-01-01", "2024-02-01"]  # Legacy alias
        assert legacy_dict["aggregated"]["days_in_period"] == [31, 29]
        assert legacy_dict["aggregated"]["ls_n_days"] == [31, 29]  # Legacy alias
        assert legacy_dict["aggregated"]["dict_v_energy"] == {"ELECTRICITY": [1000.0, 1100.0]}

        # Check detailed data
        assert "detailed" in legacy_dict
        assert legacy_dict["detailed"]["v_x"] == ["2024-01-01", "2024-02-01"]
        assert legacy_dict["detailed"]["dict_v_energy"] == {"ELECTRICITY": [1000.0, 1100.0]}

    def test_from_legacy_dict(self):
        """Test creating CalendarizedData from legacy dictionary format."""
        from better_lbnl_os.models.utility_bills import CalendarizedData

        legacy_dict = {
            "weather": {"degC": [15.0, 16.0], "degF": [59.0, 60.8]},
            "detailed": {
                "v_x": ["2024-01-01", "2024-02-01"],
                "dict_v_energy": {"ELECTRICITY": [1000.0, 1100.0]},
                "dict_v_costs": {"ELECTRICITY": [150.0, 165.0]},
                "dict_v_ghg": {"ELECTRICITY": [500.0, 550.0]},
                "dict_v_eui": {"ELECTRICITY": [0.5, 0.55]},
                "dict_v_unit_prices": {"ELECTRICITY": [0.15, 0.15]},
                "dict_v_ghg_factors": {"ELECTRICITY": [0.5, 0.5]},
            },
            "aggregated": {
                "v_x": ["2024-01-01", "2024-02-01"],
                "ls_n_days": [31, 29],
                "dict_v_energy": {"ELECTRICITY": [1000.0, 1100.0]},
                "dict_v_costs": {"ELECTRICITY": [150.0, 165.0]},
                "dict_v_ghg": {"ELECTRICITY": [500.0, 550.0]},
                "dict_v_eui": {"ELECTRICITY": [0.5, 0.55]},
                "dict_v_unit_prices": {"ELECTRICITY": [0.15, 0.15]},
                "dict_v_ghg_factors": {"ELECTRICITY": [0.5, 0.5]},
            },
        }

        data = CalendarizedData.from_legacy_dict(legacy_dict)

        # Check weather data
        assert data.weather.degC == [15.0, 16.0]
        assert data.weather.degF == [59.0, 60.8]
        assert len(data.weather.months) == 2

        # Check aggregated data
        assert len(data.aggregated.months) == 2
        assert data.aggregated.days_in_period == [31, 29]
        assert data.aggregated.energy_kwh == {"ELECTRICITY": [1000.0, 1100.0]}
        assert data.aggregated.cost == {"ELECTRICITY": [150.0, 165.0]}

        # Check detailed data
        assert len(data.detailed.months) == 2
        assert data.detailed.energy_kwh == {"ELECTRICITY": [1000.0, 1100.0]}

    def test_from_legacy_dict_short_date_format(self):
        """Test from_legacy_dict with YYYY-MM date format."""
        from better_lbnl_os.models.utility_bills import CalendarizedData

        legacy_dict = {
            "weather": {"degC": [15.0], "degF": [59.0]},
            "detailed": {
                "v_x": ["2024-01"],  # Short format
                "dict_v_energy": {},
                "dict_v_costs": {},
                "dict_v_ghg": {},
                "dict_v_eui": {},
                "dict_v_unit_prices": {},
                "dict_v_ghg_factors": {},
            },
            "aggregated": {
                "v_x": ["2024-01"],  # Short format
                "ls_n_days": [31],
                "dict_v_energy": {},
                "dict_v_costs": {},
                "dict_v_ghg": {},
                "dict_v_eui": {},
                "dict_v_unit_prices": {},
                "dict_v_ghg_factors": {},
            },
        }

        data = CalendarizedData.from_legacy_dict(legacy_dict)
        assert len(data.aggregated.months) == 1
        assert data.aggregated.months[0] == date(2024, 1, 1)

    def test_from_legacy_dict_invalid_dates_ignored(self):
        """Test that invalid dates are silently ignored during parsing."""
        from better_lbnl_os.models.utility_bills import CalendarizedData

        legacy_dict = {
            "weather": {"degC": [], "degF": []},
            "detailed": {
                "v_x": ["2024-01-01", "invalid-date", "not-a-date"],
                "dict_v_energy": {},
                "dict_v_costs": {},
                "dict_v_ghg": {},
                "dict_v_eui": {},
                "dict_v_unit_prices": {},
                "dict_v_ghg_factors": {},
            },
            "aggregated": {
                "v_x": ["2024-01-01", "bad-format"],
                "ls_n_days": [],
                "dict_v_energy": {},
                "dict_v_costs": {},
                "dict_v_ghg": {},
                "dict_v_eui": {},
                "dict_v_unit_prices": {},
                "dict_v_ghg_factors": {},
            },
        }

        data = CalendarizedData.from_legacy_dict(legacy_dict)
        # Should only parse valid dates
        assert len(data.detailed.months) == 1
        assert data.detailed.months[0] == date(2024, 1, 1)
        assert len(data.aggregated.months) == 1

    def test_from_legacy_dict_missing_keys(self):
        """Test from_legacy_dict with missing optional keys."""
        from better_lbnl_os.models.utility_bills import CalendarizedData

        legacy_dict = {}  # Empty dict

        data = CalendarizedData.from_legacy_dict(legacy_dict)
        assert data.weather is not None
        assert data.aggregated is not None
        assert data.detailed is not None
        assert len(data.weather.degC) == 0
        assert len(data.aggregated.months) == 0

    def test_roundtrip_legacy_conversion(self):
        """Test that to_legacy_dict and from_legacy_dict are reversible."""
        from better_lbnl_os.models.utility_bills import (
            CalendarizedData,
            EnergyAggregation,
            FuelAggregation,
        )
        from better_lbnl_os.models.weather import WeatherSeries

        # Create original data
        months = [date(2024, 1, 1), date(2024, 2, 1)]
        original = CalendarizedData(
            weather=WeatherSeries(months=months, degC=[15.0, 16.0], degF=[59.0, 60.8]),
            aggregated=EnergyAggregation(
                months=months,
                days_in_period=[31, 29],
                energy_kwh={"ELECTRICITY": [1000.0, 1100.0]},
                cost={"ELECTRICITY": [150.0, 165.0]},
                ghg_kg={},
                daily_eui_kwh_per_m2={},
                unit_price_per_kwh={},
                unit_emission_kg_per_kwh={},
            ),
            detailed=FuelAggregation(
                months=months,
                days_in_period=[31, 29],
                energy_kwh={"ELECTRICITY": [1000.0, 1100.0]},
                cost={},
                ghg_kg={},
                daily_eui_kwh_per_m2={},
                unit_price_per_kwh={},
                unit_emission_kg_per_kwh={},
            ),
        )

        # Convert to legacy and back
        legacy_dict = original.to_legacy_dict()
        restored = CalendarizedData.from_legacy_dict(legacy_dict)

        # Verify data is preserved
        assert restored.weather.degC == original.weather.degC
        assert restored.weather.degF == original.weather.degF
        assert len(restored.aggregated.months) == len(original.aggregated.months)
        assert restored.aggregated.days_in_period == original.aggregated.days_in_period
        assert restored.aggregated.energy_kwh == original.aggregated.energy_kwh
