# BETTER-LBNL

[![CI](https://github.com/LBNL-ETA/better-lbnl-os/actions/workflows/ci.yml/badge.svg)](https://github.com/LBNL-ETA/better-lbnl-os/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/LBNL-ETA/better-lbnl-os/branch/main/graph/badge.svg)](https://codecov.io/gh/LBNL-ETA/better-lbnl-os)
[![PyPI version](https://badge.fury.io/py/better-lbnl-os.svg)](https://badge.fury.io/py/better-lbnl-os)
[![Python Versions](https://img.shields.io/pypi/pyversions/better-lbnl-os.svg)](https://pypi.org/project/better-lbnl-os/)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Documentation Status](https://readthedocs.org/projects/better-lbnl-os/badge/?version=latest)](https://better-lbnl-os.readthedocs.io/en/latest/?badge=latest)

Open-source Python library for building energy analytics, serving as the analytical engine underlying the [BETTER web application](https://better.lbl.gov) (Building Efficiency Targeting Tool for Energy Retrofits).

## Features

- **Change-point Model Fitting**: Automated fitting of 1P, 3P, and 5P change-point models for building energy analysis
- **Building Benchmarking**: Statistical comparison of building performance against peer groups
- **Energy Savings Estimation**: Weather-normalized savings calculations with uncertainty quantification
- **EE Measure Recommendations**: Rule-based recommendations for energy efficiency improvements
- **Portfolio Analytics**: Aggregate analysis across multiple buildings

## Installation

### Using pip

```bash
pip install better-lbnl-os
```

### Using uv (recommended)

```bash
uv add better-lbnl-os
```

### Development Installation

```bash
git clone https://github.com/LBNL-ETA/better-lbnl-os.git
cd better-lbnl-os
uv venv
uv pip install -e ".[dev]"
```

## Quick Start

```python
from better_lbnl_os import fit_changepoint_model
import numpy as np

# Prepare temperature and energy data (showing heating and cooling patterns)
temperatures = np.array([30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85])  # °F
energy_use = np.array([150, 140, 125, 110, 95, 85, 80, 80, 85, 95, 110, 125])  # kBtu/day

# Fit change-point model
model_result = fit_changepoint_model(temperatures, energy_use)

# Check model quality
if model_result.is_valid():
    print(f"Model Type: {model_result.model_type}")  # 5P (heating and cooling)
    print(f"R-squared: {model_result.r_squared:.3f}")  # 0.995
    print(f"Baseload: {model_result.baseload:.1f}")  # 80.0
```

## Documentation

Full documentation is available at [https://better-lbnl-os.readthedocs.io](https://better-lbnl-os.readthedocs.io)

### Key Concepts

- **Domain Models**: Rich objects that encapsulate both data and business logic
- **Pure Functions**: Mathematical algorithms implemented as side-effect-free functions
- **Service Layer**: Orchestration of complex workflows
- **Adapter Pattern**: Clean separation for framework integration

## Examples

See the `examples/` directory for:

- `benchmarking_demo.py` - Building benchmarking demonstration
- `notebooks/explore.ipynb` - Interactive exploration notebook
- `weather/` - Weather data integration examples

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
pytest --cov=better_lbnl_os --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest tests/unit/    # Only unit tests
```

## License

This project is licensed under a modified BSD license with additional DOE government clauses - see the [LICENSE](LICENSE) and [COPYRIGHT](COPYRIGHT) files for details.

## Citation

If you use BETTER-LBNL-OS in your research, please cite:

```bibtex
@software{better_lbnl_os,
  author = {Li, Han},
  title = {BETTER-LBNL-OS: Open-Source Building Energy Analytics Library},
  year = {2025},
  publisher = {Lawrence Berkeley National Laboratory},
  url = {https://github.com/LBNL-ETA/better-lbnl-os}
}
```

## Contact

- **Author**: Han Li (hanli@lbl.gov)
- **Project Manager**: Carolyn Szum (cszum@lbl.gov)
- **Organization**: Lawrence Berkeley National Laboratory

## Acknowledgments

This work was supported by the U.S. Department of Energy's Building Technologies Office. BETTER is part of the [DOE Building Data Tools](https://buildingdata.energy.gov/) ecosystem.

- **DOE Program Manager**: Billierae Engelman
- **Cooperative Research and Development Agreement (CRADA) Partner**: Johnson Controls, Inc. (benchmarking methodology and LEAN Energy Analysis)

## Related Projects

- [BETTER Web Application](https://better.lbl.gov): The full web-based building analysis platform
- [BuildingSync](https://buildingsync.net): Schema for building data exchange
- [SEED Platform](https://seed-platform.org): Standard Energy Efficiency Data Platform
