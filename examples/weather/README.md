# Weather Module Examples

This directory contains examples demonstrating how to use the BETTER-LBNL weather module for retrieving weather data and performing energy-related calculations.

## Examples

### 1. `simple_weather_example.py`
**Minimal example** showing the basics:
- Get weather data for a location
- Calculate heating and cooling degree days
- Display temperature information

Perfect for getting started quickly.

### 2. `get_weather_data.py`
**Comprehensive examples** including:
- Getting monthly weather data
- Retrieving annual weather patterns
- Comparing weather across multiple locations
- Finding weather stations
- Using custom base temperatures for degree day calculations

Great for understanding all the features available.

### 3. `weather_for_energy_analysis.py`
**Energy analysis examples** demonstrating:
- Aligning weather data with utility billing periods
- Correlating energy consumption with weather
- Identifying heating vs. cooling dominated buildings
- Weather-normalizing energy consumption
- Comparing actual vs. typical weather years

Essential for building energy analysts.

## Running the Examples

Make sure you have the BETTER-LBNL package installed:

```bash
# From the better-lbnl-os directory
pip install -e .
```

Then run any example:

```bash
python examples/weather/simple_weather_example.py
```

## Key Concepts

### Degree Days
- **Heating Degree Days (HDD)**: Measure of how much and for how long the outside temperature was below a base temperature (typically 65°F/18.3°C)
- **Cooling Degree Days (CDD)**: Measure of how much and for how long the outside temperature was above a base temperature

### Weather Providers
The examples use the **OpenMeteo** provider, which:
- Provides free access to historical weather data globally
- Uses gridded data (not physical weather stations)
- Covers data from 1940 to present
- Has both free and commercial tiers

### Location Information
Weather data is retrieved using geographic coordinates (latitude/longitude). The `LocationInfo` object can also store:
- ZIP code
- State/province
- Weather station IDs
- eGrid subregion (for emissions calculations)

## Common Use Cases

### Building Energy Analysis
```python
# Get weather aligned with utility bills
weather = service.get_weather_data(location, year, month)
hdd = weather.calculate_hdd()  # For heating analysis
cdd = weather.calculate_cdd()  # For cooling analysis
```

### Climate Comparison
```python
# Compare different locations or time periods
weather_2022 = service.get_weather_range(location, 2022, 1, 2022, 12)
weather_2023 = service.get_weather_range(location, 2023, 1, 2023, 12)
```

### Custom Analysis
```python
# Use different base temperatures for specialized applications
hdd_60 = weather.calculate_hdd(base_temp_f=60.0)  # Commercial buildings
hdd_70 = weather.calculate_hdd(base_temp_f=70.0)  # Sensitive populations
```

## API Limits

OpenMeteo Free Tier:
- 10,000 requests per day
- No API key required
- Full historical data access

OpenMeteo Commercial Tier:
- 100,000+ requests per day
- API key required
- Priority support

## Next Steps

1. **Integrate with your application**: Use the weather service in your energy analysis tools
2. **Add more providers**: Extend with NOAA, Weather Underground, or other providers
3. **Cache results**: Store retrieved weather data to reduce API calls
4. **Batch processing**: Process multiple buildings or periods efficiently

## Support

For questions or issues with the weather module, please refer to the main BETTER-LBNL documentation or open an issue on GitHub.
