# Test Suite Organization

This directory contains the complete test suite for the `better-lbnl-os` package.

## Directory Structure

```
tests/
├── unit/                          # Fast, isolated unit tests (no I/O, mocked dependencies)
│   ├── core/                      # Tests for core business logic
│   │   ├── test_changepoint.py   # Change-point model algorithms
│   │   ├── test_benchmarking.py  # Statistical benchmarking functions
│   │   ├── test_preprocessing.py # Calendarization and data prep
│   │   ├── test_weather_service.py    # Weather service orchestration
│   │   └── test_weather_providers.py  # Weather data providers (OpenMeteo, NOAA)
│   │
│   ├── models/                    # Tests for domain models (Pydantic)
│   │   ├── test_building.py      # BuildingData model
│   │   ├── test_utility_bills.py # UtilityBillData model
│   │   └── test_weather.py       # WeatherData, WeatherStation models
│   │
│   ├── utils/                     # Tests for pure utility functions
│   │   ├── test_calculations.py  # Temperature conversions, averages
│   │   └── test_geocoding.py     # Geography utilities (haversine, validation)
│   │
│   └── io/                        # Tests for I/O adapters
│       └── test_energy_conversions.py  # Fuel/unit normalization
│
├── integration/                   # End-to-end workflow tests (slower, real I/O)
│   └── (TODO: add integration tests covering complete workflows)
│
├── fixtures/                      # Test data and fixtures
│   ├── templates/                # Sample Excel/CSV templates
│   ├── reference_stats/          # Benchmark reference statistics
│   └── weather/                  # Sample weather data
│
├── conftest.py                   # Shared pytest fixtures
└── README.md                     # This file
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run only unit tests (fast)
```bash
pytest tests/unit/ -v
```

### Run tests for a specific module
```bash
pytest tests/unit/core/test_changepoint.py
pytest tests/unit/models/test_building.py
```

### Run with coverage report
```bash
pytest tests/ --cov=better_lbnl_os --cov-report=html
```

### Skip slow tests
```bash
pytest tests/ -m "not slow"
```

### Run only integration tests
```bash
pytest tests/integration/ -v
```

## Test Categories

Tests are organized by **layer** and **responsibility**:

### Unit Tests (`tests/unit/`)
- **Fast** (< 100ms per test)
- **Isolated** (no network, no file I/O)
- **Mocked** dependencies (use pytest fixtures)
- **Purpose**: Validate individual functions, classes, methods

### Integration Tests (`tests/integration/`)
- **Slower** (can take seconds)
- **Real I/O** (file reads, API calls, database)
- **Purpose**: Validate complete workflows end-to-end
- **Mark with**: `@pytest.mark.integration`

## Writing New Tests

### Follow the Mirror Principle
Test structure mirrors source code structure:

- `src/better_lbnl_os/core/changepoint.py` → `tests/unit/core/test_changepoint.py`
- `src/better_lbnl_os/models/building.py` → `tests/unit/models/test_building.py`
- `src/better_lbnl_os/utils/calculations.py` → `tests/unit/utils/test_calculations.py`

### Use Shared Fixtures
Common test data is defined in `conftest.py`:

```python
def test_something(sample_building, sample_electricity_bill):
    # sample_building and sample_electricity_bill are automatically available
    assert sample_building.floor_area == 50000
```

### Test Naming Convention
- File: `test_<module_name>.py`
- Class: `Test<FeatureName>` or `Test<ClassName>`
- Method: `test_<what_is_being_tested>`

Example:
```python
class TestChangePointModeling:
    def test_fit_simple_1p_model(self):
        ...
```

## Coverage Goals

- **Target**: 80% overall coverage
- **Core modules**: 90%+ coverage (changepoint, benchmarking, preprocessing)
- **Models**: 85%+ coverage (validation logic must be tested)
- **Utils**: 90%+ coverage (pure functions should be fully tested)

## Current Status

- **Total Tests**: 104
- **Passing**: 98
- **Failing**: 5 (known issues, being fixed)
- **Skipped**: 1 (feature not implemented)
- **Coverage**: 51.4% (working toward 80% target)

Run `pytest tests/ --cov=better_lbnl_os --cov-report=term-missing` to see detailed coverage report.
