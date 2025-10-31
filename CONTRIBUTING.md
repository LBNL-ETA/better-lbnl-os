# Contributing to BETTER-LBNL

We love your input! We want to make contributing to BETTER-LBNL as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git

### Setup Instructions

1. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/better-lbnl.git
   cd better-lbnl
   ```

2. **Create a virtual environment with uv**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the package in development mode**
   ```bash
   uv pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Code Style

We use several tools to maintain code quality:

- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **Ruff** for linting
- **mypy** for type checking

Run all checks:
```bash
# Format code
black src tests
isort src tests

# Lint
ruff check src tests

# Type check
mypy src
```

Or use pre-commit to run all checks:
```bash
pre-commit run --all-files
```

## Testing

We use pytest for testing. Write tests for any new functionality.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=better_lbnl --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run tests matching a pattern
pytest -k "test_building"

# Skip slow tests
pytest -m "not slow"
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use fixtures for common test data
- Mock external dependencies
- Aim for >80% code coverage

Example test:
```python
def test_building_calculate_eui():
    """Test EUI calculation for BuildingData."""
    building = BuildingData(
        name="Test Building",
        floor_area=10000,
        space_type="Office",
        location="Berkeley, CA"
    )
    
    # 34,120 kWh = 116,441.44 kBtu
    # 116,441.44 kBtu / 10,000 sqft = 11.64 kBtu/sqft
    eui = building.calculate_eui(annual_energy_kwh=34120)
    assert abs(eui - 11.64) < 0.01
```

## Documentation

We use Sphinx for documentation. Update docs for any API changes.

### Building Documentation

```bash
cd docs
make html
# Open _build/html/index.html in a browser
```

### Writing Documentation

- Use Google-style docstrings
- Include type hints
- Provide examples in docstrings
- Update API reference for new modules

Example docstring:
```python
def calculate_eui(self, annual_energy_kwh: float) -> float:
    """Calculate Energy Use Intensity (kBtu/sqft/year).
    
    Args:
        annual_energy_kwh: Annual energy consumption in kWh
        
    Returns:
        EUI in kBtu/sqft/year
        
    Example:
        >>> building = BuildingData(name="Office", floor_area=10000, ...)
        >>> eui = building.calculate_eui(34120)
        >>> print(f"EUI: {eui:.1f} kBtu/sqft/year")
        EUI: 11.6 kBtu/sqft/year
    """
```

## Pull Request Process

1. **Update CHANGELOG.md** with details of changes
2. **Update README.md** if needed
3. **Ensure all tests pass** locally
4. **Update documentation** if you changed APIs
5. **Request review** from maintainers
6. **Address feedback** promptly

### PR Title Format

Use conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

Examples:
- `feat: add portfolio benchmarking service`
- `fix: correct EUI calculation for metric units`
- `docs: add examples for change-point modeling`

## Reporting Bugs

Use GitHub issues to report bugs. Include:

- **Summary** of the issue
- **Steps to reproduce**
  - Be specific!
  - Give sample code if you can
- **Expected behavior**
- **Actual behavior**
- **Environment details**
  - Python version
  - OS
  - Package versions (`uv pip list`)

## Feature Requests

We love feature requests! Use GitHub issues with:

- **Problem description** - what problem does this solve?
- **Proposed solution** - how would you like it to work?
- **Alternatives considered** - what other solutions did you think about?
- **Additional context** - mockups, examples, etc.

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

Examples of behavior that contributes to creating a positive environment:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at hanli@lbl.gov.

## Recognition

Contributors will be recognized in:
- The CHANGELOG.md file
- The GitHub contributors page
- Project documentation

## Questions?

Feel free to:
- Open a [discussion](https://github.com/LBNL-ETA/better-lbnl/discussions)
- Contact the maintainer: hanli@lbl.gov
- Check existing [issues](https://github.com/LBNL-ETA/better-lbnl/issues)

Thank you for contributing to BETTER-LBNL! 🎉