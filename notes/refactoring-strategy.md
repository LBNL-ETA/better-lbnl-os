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

### Option 2: Domain Models with Behavior (Recommended Component)

**Approach**: Create rich domain models using Pydantic/dataclasses that include both data and business logic methods.

**Advantages**:
- Encapsulates business rules within domain objects
- Self-validating and self-documenting
- More intuitive API with methods like `building.calculate_eui()`
- Better code organization

**Disadvantages**:
- Requires thoughtful design of domain boundaries
- Need to carefully separate Django-specific code
- Initial learning curve for domain-driven design

**Implementation Example**:
```python
# Library: better_lbnl/domain/models.py
from pydantic import BaseModel, Field
from typing import Optional

class ChangePointModelResult(BaseModel):
    """Domain model with data + business logic methods"""
    heating_slope: Optional[float]
    cooling_slope: Optional[float]
    baseload: float
    r_squared: float
    cvrmse: float
    
    def is_valid(self) -> bool:
        """Check if model meets quality thresholds"""
        return self.r_squared >= 0.6 and self.cvrmse <= 0.5
    
    def get_model_type(self) -> str:
        """Determine model type from coefficients"""
        if self.heating_slope and self.cooling_slope:
            return "5P"
        elif self.heating_slope:
            return "3P-H"
        elif self.cooling_slope:
            return "3P-C"
        return "1P"

# Pure function for algorithm
def fit_changepoint_model(temp: np.ndarray, energy: np.ndarray) -> ChangePointModelResult:
    # Fitting logic
    return ChangePointModelResult(
        heating_slope=hsl,
        cooling_slope=csl,
        baseload=base,
        r_squared=r2,
        cvrmse=cv
    )

# Django adapter
class InverseModelAdapter:
    def fit_model(self, django_model):
        from better_lbnl import fit_changepoint_model
        result = fit_changepoint_model(django_model.temps, django_model.eui)
        # Use domain model methods
        if result.is_valid():
            django_model.model_coeffs = result.dict()
            django_model.model_type = result.get_model_type()
            django_model.save()
```

### Option 3: Adapter Pattern (Recommended for Django Integration)

**Approach**: Create adapter layer in Django app to bridge between Django models and the pure Python library.

**Advantages**:
- Complete separation of concerns
- Framework-agnostic library
- Django app changes are isolated to adapter layer
- Easy to test library independently
- Most flexible for future changes

**Disadvantages**:
- Additional adapter layer to maintain
- Initial setup complexity
- Need to maintain mappings between Django and domain models

**This is the recommended integration approach** - adapters provide clean separation while minimizing disruption to existing Django code.

## Recommended Approach: Hybrid Strategy with Domain Models

Based on architectural review, we recommend a **hybrid approach** that combines the best of all options:

### Core Architecture Components

1. **Pure Functions for Algorithms**: Mathematical algorithms (change-point fitting, statistical calculations) as pure functions
2. **Rich Domain Models**: Pydantic/dataclass models that include both data AND business logic methods
3. **Service Layer**: Orchestration classes that coordinate between domain models and algorithms
4. **Adapter Pattern**: Clean separation between Django and the library through adapter layers

### Implementation Phases

#### Phase 1: Domain Models with Behavior (Week 1-2)
- Create Pydantic models that encapsulate both data and methods
- Example: `BuildingData` with methods like `calculate_eui()`, `validate_bills()`
- Domain models handle their own validation, conversion, and business rules

#### Phase 2: Extract Pure Algorithms (Week 3-4)
- Extract mathematical functions as pure, side-effect-free functions
- Focus on ChangePointModel fitting, benchmark calculations, statistical utilities
- Functions take simple inputs (arrays, primitives) and return domain models or dataclasses

#### Phase 3: Build Service Layer (Week 5-6)
- Create service classes that orchestrate complex workflows
- Services use both domain models and pure functions
- Example: `BuildingAnalyticsService` that coordinates the full analysis pipeline

#### Phase 4: Implement Adapter Pattern (Week 7-8)
- Create adapter layer in Django app (NOT in the library)
- Adapters convert between Django models and domain models
- This is the ONLY place where Django touches the library
- Ensures complete framework independence

## Implementation Plan

### Directory Structure
```
better-lbnl/
├── src/
│   └── better_lbnl/
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
1. Add better-lbnl as dependency
2. Create adapter layer in Django app
3. Import library through adapters only
4. Replace internal implementation gradually
5. Run integration tests
6. Verify backward compatibility

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