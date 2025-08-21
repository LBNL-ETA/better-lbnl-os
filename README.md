# BETTER-LBNL

[![CI](https://github.com/LBNL-ETA/better-lbnl/actions/workflows/ci.yml/badge.svg)](https://github.com/LBNL-ETA/better-lbnl/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/LBNL-ETA/better-lbnl/branch/main/graph/badge.svg)](https://codecov.io/gh/LBNL-ETA/better-lbnl)
[![PyPI version](https://badge.fury.io/py/better-lbnl.svg)](https://badge.fury.io/py/better-lbnl)
[![Python Versions](https://img.shields.io/pypi/pyversions/better-lbnl.svg)](https://pypi.org/project/better-lbnl/)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Documentation Status](https://readthedocs.org/projects/better-lbnl/badge/?version=latest)](https://better-lbnl.readthedocs.io/en/latest/?badge=latest)

Open-source Python library for building energy analytics, extracted from BETTER (Building Efficiency Targeting Tool for Energy Retrofits).

## Features

- **Change-point Model Fitting**: Automated fitting of 1P, 3P, and 5P change-point models for building energy analysis
- **Building Benchmarking**: Statistical comparison of building performance against peer groups
- **Energy Savings Estimation**: Weather-normalized savings calculations with uncertainty quantification
- **EE Measure Recommendations**: Rule-based recommendations for energy efficiency improvements
- **Portfolio Analytics**: Aggregate analysis across multiple buildings

## Installation

### Using pip

```bash
pip install better-lbnl
```

### Using uv (recommended)

```bash
uv add better-lbnl
```

### Development Installation

```bash
git clone https://github.com/LBNL-ETA/better-lbnl.git
cd better-lbnl
uv venv
uv pip install -e ".[dev]"
```

## Quick Start

```python
from better_lbnl import BuildingData, fit_changepoint_model
import numpy as np

# Create a building
building = BuildingData(
    name="Office Building A",
    floor_area=50000,  # sq ft
    space_type="Office",
    location="Berkeley, CA"
)

# Prepare temperature and energy data
temperatures = np.array([45, 50, 55, 60, 65, 70, 75, 80])  # °F
energy_use = np.array([120, 110, 95, 85, 80, 82, 95, 115])  # kWh/day/1000sqft

# Fit change-point model
model_result = fit_changepoint_model(temperatures, energy_use)

# Check model quality
if model_result.is_valid():
    print(f"Model Type: {model_result.model_type}")
    print(f"R-squared: {model_result.r_squared:.3f}")
    print(f"Baseload: {model_result.baseload:.1f}")
```

## Documentation

Full documentation is available at [https://better-lbnl.readthedocs.io](https://better-lbnl.readthedocs.io)

### Key Concepts

- **Domain Models**: Rich objects that encapsulate both data and business logic
- **Pure Functions**: Mathematical algorithms implemented as side-effect-free functions
- **Service Layer**: Orchestration of complex workflows
- **Adapter Pattern**: Clean separation for framework integration

## Examples

See the `examples/` directory for Jupyter notebooks demonstrating:

- Basic change-point model fitting
- Portfolio benchmarking
- Building energy analysis workflow
- Integration with web frameworks

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install development dependencies (`uv pip install -e ".[dev]"`)
4. Make your changes
5. Run tests (`pytest`)
6. Run linting (`ruff check . && black . && mypy src`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=better_lbnl --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest tests/unit/    # Only unit tests
```

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use BETTER-LBNL in your research, please cite:

```bibtex
@software{better_lbnl,
  author = {Li, Han and others},
  title = {BETTER-LBNL: Building Energy Analytics Library},
  year = {2025},
  publisher = {Lawrence Berkeley National Laboratory},
  url = {https://github.com/LBNL-ETA/better-lbnl}
}
```

## Acknowledgments

This work was supported by the U.S. Department of Energy's Building Technologies Office.

## Contact

- **Author**: Han Li (hanli@lbl.gov)
- **Organization**: Lawrence Berkeley National Laboratory
- **Project**: [BETTER](https://better.lbl.gov)

## Related Projects

- [BETTER Web Application](https://better.lbl.gov): The full web-based building analysis platform
- [BuildingSync](https://buildingsync.net): Schema for building data exchange
- [SEED Platform](https://seed-platform.org): Standard Energy Efficiency Data Platform