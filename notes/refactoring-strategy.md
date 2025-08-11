# BETTER Core Library Extraction Strategy

## Executive Summary
This document outlines strategies for extracting core business logic from the BETTER Django web application into a standalone, open-source Python library. The goal is to create a reusable library while minimizing refactoring overhead in the existing Django application.

## Current Architecture Analysis

### Core Components Identified
1. **Inverse Modeling**: Change-point models for building energy analysis
2. **Benchmarking**: Statistical comparison against reference buildings
3. **EEM Recommendations**: Rule-based energy efficiency measure suggestions
4. **Analytics Calculations**: Energy, cost, and GHG emissions calculations
5. **Weather Processing**: HDD/CDD calculations and normalization
6. **Utility Functions**: Unit conversions, validations, statistics

### Key Dependencies
- **Scientific Computing**: numpy, scipy, pandas
- **Visualization**: plotly
- **External APIs**: NREL PVWatts, NOAA Weather
- **Django-specific**: ORM, JSONField, Celery, signals

## Refactoring Strategy Options

### Option 1: Direct Function Extraction (Minimal Refactoring)

**Approach**: Extract core algorithms as pure Python functions that accept and return basic Python types (dict, list, numpy arrays).

**Advantages**:
- Minimal code changes required
- No data mapping layers needed
- JSONFields remain unchanged
- Quick implementation timeline
- Easy to test in isolation

**Disadvantages**:
- Less object-oriented design
- May lead to function proliferation
- Limited type safety without classes

**Implementation Example**:
```python
# Library: better_core/models/changepoint.py
def fit_changepoint_model(temperature: np.ndarray, 
                          energy_use: np.ndarray,
                          min_r_squared: float = 0.6) -> dict:
    """
    Fits a 5-parameter change-point model.
    Returns dict compatible with Django JSONField.
    """
    # Core algorithm logic here
    return {
        'heating_slope': hsl,
        'heating_changepoint': hcp,
        'baseload': base,
        'cooling_changepoint': ccp,
        'cooling_slope': csl,
        'r_squared': r2,
        'cv_rmse': cv
    }

# Django app usage
class BuildingAnalytics(models.Model):
    model_coefficients = JSONField()
    
    def run_inverse_model(self):
        from better_core.models import fit_changepoint_model
        self.model_coefficients = fit_changepoint_model(
            self.get_temperatures(), 
            self.get_energy_use()
        )
        self.save()
```

### Option 2: Class Extraction Without ORM (Moderate Refactoring)

**Approach**: Keep existing class structures but remove Django dependencies. Classes return dictionaries or simple dataclasses instead of Django models.

**Advantages**:
- Preserves object-oriented design
- Better encapsulation of related logic
- Easier state management
- More intuitive API

**Disadvantages**:
- Requires more refactoring
- Need to carefully separate Django-specific code
- May require some interface changes

**Implementation Example**:
```python
# Library: better_core/models/changepoint.py
class ChangePointModel:
    """Pure Python implementation without Django dependencies"""
    
    def __init__(self, temperature: np.ndarray, eui: np.ndarray, **kwargs):
        self.temperature = temperature
        self.eui = eui
        self.min_r_squared = kwargs.get('min_r_squared', 0.6)
        
    def fit(self) -> dict:
        # Fitting logic
        return {
            'coefficients': self.coefficients,
            'metrics': self.metrics
        }

# Django wrapper
class InverseModel(models.Model):
    model_coeffs = JSONField()
    
    def fit_model(self):
        from better_core.models import ChangePointModel
        model = ChangePointModel(self.temps, self.eui)
        self.model_coeffs = model.fit()
        self.save()
```

### Option 3: Full Abstraction with Adapters (Maximum Flexibility)

**Approach**: Create complete abstraction layer with dataclasses/Pydantic models and adapter pattern for Django integration.

**Advantages**:
- Complete separation of concerns
- Framework-agnostic library
- Strong type safety
- Most flexible for future changes

**Disadvantages**:
- Significant refactoring required
- Complexity of adapter layers
- Longer implementation timeline
- Potential performance overhead

**Not recommended for initial implementation** due to complexity.

## Recommended Approach: Hybrid Strategy

### Phase 1: Start with Option 1 (Quick Wins)
- Extract pure mathematical functions
- Focus on ChangePointModel algorithms
- Benchmark calculations
- Statistical utilities

### Phase 2: Move to Option 2 (Consolidation)
- Refactor related functions into classes
- Group functionality logically
- Add better error handling
- Improve API design

### Phase 3: Enhance as Needed
- Add type hints throughout
- Consider Pydantic for complex data structures
- Optimize performance-critical sections
- Add comprehensive documentation

## Implementation Plan

### Directory Structure
```
better-core/
├── src/
│   └── better_core/
│       ├── __init__.py
│       ├── models/
│       │   ├── changepoint.py      # Inverse modeling
│       │   └── coefficients.py     # Model results
│       ├── benchmarking/
│       │   ├── statistics.py       # Reference stats
│       │   └── comparison.py       # Benchmark logic
│       ├── measures/
│       │   ├── constants.py        # EEM definitions
│       │   └── recommendations.py  # Rule engine
│       ├── analytics/
│       │   ├── energy.py          # Energy calculations
│       │   ├── savings.py         # Savings analysis
│       │   └── portfolio.py       # Aggregations
│       ├── weather/
│       │   └── processing.py      # HDD/CDD calculations
│       └── utils/
│           ├── conversions.py     # Unit conversions
│           └── validators.py      # Data validation
├── tests/
├── docs/
└── pyproject.toml
```

### Priority Components for Extraction

#### High Priority (Core Value)
1. **ChangePointModel** - Core inverse modeling algorithm
2. **EEM Recommendation Logic** - Rule-based recommendations
3. **Benchmark Calculations** - Statistical comparisons
4. **Energy Calculations** - Consumption and savings

#### Medium Priority (Supporting Features)
1. **Weather Processing** - HDD/CDD calculations
2. **Unit Conversions** - SI/IP conversions
3. **Portfolio Aggregation** - Multi-building analytics
4. **Statistical Utilities** - Common calculations

#### Low Priority (Keep in Django)
1. **File Upload/Parsing** - Web-specific functionality
2. **API Serialization** - REST framework specific
3. **Celery Task Management** - Async processing
4. **User Authentication** - Django auth system
5. **Database Models** - ORM relationships

## Migration Strategy

### Step 1: Setup Library Project
```bash
# Create new library project
mkdir better-core
cd better-core
python -m venv venv
source venv/bin/activate

# Setup project structure
touch pyproject.toml
mkdir -p src/better_core tests docs
```

### Step 2: Extract First Component
1. Copy ChangePointModel class to library
2. Remove Django imports
3. Replace Django-specific features
4. Add comprehensive tests
5. Verify output matches original

### Step 3: Update Django App
1. Add better-core as dependency
2. Import library functions
3. Replace internal implementation
4. Run integration tests
5. Verify backward compatibility

### Step 4: Iterate
1. Extract next component
2. Test thoroughly
3. Update Django app
4. Document changes
5. Repeat for all components

## Testing Strategy

### Library Testing
```python
# tests/test_changepoint.py
def test_changepoint_model():
    temps = np.array([...])
    energy = np.array([...])
    
    result = fit_changepoint_model(temps, energy)
    
    assert 'heating_slope' in result
    assert result['r_squared'] > 0.6
    # Compare with known good outputs
```

### Integration Testing
```python
# Django app tests
def test_django_library_integration():
    # Create test building with data
    building = BuildingFactory()
    
    # Run analysis using library
    analytics = building.run_analytics()
    
    # Verify results match expected
    assert analytics.model_coefficients == expected
```

## Documentation Requirements

### Library Documentation
- API reference for all public functions/classes
- Usage examples for common scenarios
- Migration guide from Django methods
- Performance considerations
- Contributing guidelines

### Django App Updates
- Update references to use library
- Document any API changes
- Provide upgrade path for users
- Maintain backward compatibility

## Success Metrics

1. **Code Reusability**: Library usable in non-Django contexts
2. **Performance**: No degradation in processing speed
3. **Accuracy**: Results identical to current implementation
4. **Maintainability**: Reduced code duplication
5. **Testing**: >90% test coverage for library
6. **Documentation**: Complete API documentation
7. **Adoption**: Successfully used in multiple projects

## Risk Mitigation

### Technical Risks
- **Data Format Changes**: Use versioning for data structures
- **Performance Issues**: Profile and optimize critical paths
- **Breaking Changes**: Maintain compatibility layer during transition

### Process Risks
- **Scope Creep**: Focus on core algorithms first
- **Timeline Delays**: Use phased approach
- **Testing Gaps**: Comprehensive test suite before migration

## Next Steps

1. Review and approve strategy
2. Set up better-core repository
3. Create initial project structure
4. Extract ChangePointModel as proof of concept
5. Validate approach with stakeholders
6. Continue with prioritized components

## Appendix: Component Dependencies

### ChangePointModel Dependencies
- numpy: Numerical computations
- scipy: Optimization and statistics
- No Django dependencies after extraction

### EEM Recommendations Dependencies
- Constants definitions
- Coefficient comparison logic
- No external API calls

### Benchmarking Dependencies
- Reference statistics (JSON file)
- Statistical calculations
- Building type mappings

### Portfolio Analytics Dependencies
- Individual building analytics
- Aggregation functions
- Summary statistics

---

*Document Version: 1.0*  
*Last Updated: 2025-01-11*  
*Author: BETTER Development Team*