# Package Structure Reorganization Plan

## Current vs Planned Structure Analysis

### Key Differences Identified

#### 1. Core Module Organization
**Current Structure:**
```
core/
├── algorithms/           # Scattered algorithms
│   ├── changepoint.py
│   ├── geocoding.py
│   ├── statistics.py
│   └── weather.py
└── weather/             # Weather-specific subsystem
    ├── interfaces.py
    ├── providers.py
    └── service.py
```

**Planned Structure:**
```
core/                    # Flat structure for core algorithms
├── changepoint.py
├── benchmarking.py
├── savings.py
└── recommendations.py
```

**Issues:**
- Current has nested `algorithms/` directory - adds unnecessary depth
- Weather functionality split between `core/algorithms/weather.py` and `core/weather/`
- Missing core algorithms: benchmarking, savings, recommendations

#### 2. Data Module Purpose
**Current Structure:**
```
data/                    # Empty directory
domain/                  # Contains models and services
├── models.py           # All domain models here
└── services.py         # Service layer
```

**Planned Structure:**
```
data/                    # Data structures and validation
├── models.py           # Domain models (DTOs)
├── constants.py        # Physical constants
└── validators.py       # Input validation
```

**Issues:**
- Domain models currently in `domain/` instead of `data/`
- Missing constants.py and validators.py
- Service layer wasn't in original plan but adds value

#### 3. Utils Module Content
**Current Structure:**
```
utils/
└── geography.py        # Only geography utilities
```

**Planned Structure:**
```
utils/
├── unit_conversion.py
├── statistics.py       # Currently in core/algorithms/
└── weather.py         # Currently in core/algorithms/
```

**Issues:**
- Missing unit_conversion.py
- statistics.py and weather.py are in wrong location
- geography.py wasn't in original plan but is useful

#### 4. Interfaces Module
**Current Structure:**
```
interfaces/             # Empty directory
core/weather/
└── interfaces.py      # Weather interfaces in wrong location
```

**Planned Structure:**
```
interfaces/
├── weather_source.py
└── benchmark_source.py
```

**Issues:**
- Weather interfaces in wrong location
- Missing benchmark_source interface

## Reorganization Plan

### Phase 1: Restructure Core Module (Priority: High)
1. **Flatten the core structure:**
   - Move `core/algorithms/changepoint.py` → `core/changepoint.py`
   - Delete empty `core/algorithms/` directory
   
2. **Consolidate weather functionality:**
   - Keep weather service architecture but reorganize:
   - Move `core/weather/interfaces.py` → `interfaces/weather_source.py`
   - Keep `core/weather/providers.py` and `core/weather/service.py` as implementation details

3. **Add missing core algorithms:**
   - Create `core/benchmarking.py`
   - Create `core/savings.py`
   - Create `core/recommendations.py`

### Phase 2: Reorganize Data/Domain Modules (Priority: High)
1. **Merge domain into data:**
   - Move `domain/models.py` → `data/models.py`
   - Keep `domain/services.py` → `data/services.py` (value-add)
   
2. **Add missing data components:**
   - Create `data/constants.py` for energy conversion factors
   - Create `data/validators.py` for input validation

3. **Remove domain directory** after migration

### Phase 3: Reorganize Utils Module (Priority: Medium)
1. **Move utilities to correct location:**
   - Move `core/algorithms/statistics.py` → `utils/statistics.py`
   - Move `core/algorithms/weather.py` → `utils/weather.py`
   - Keep `utils/geography.py` (useful addition)
   
2. **Add missing utilities:**
   - Create `utils/unit_conversion.py`

### Phase 4: Complete Interfaces Module (Priority: Medium)
1. **Move existing interfaces:**
   - Move `core/weather/interfaces.py` → `interfaces/weather_source.py`
   
2. **Create missing interfaces:**
   - Create `interfaces/benchmark_source.py`
   - Create `interfaces/measure_database.py` (from workplan)

### Phase 5: Handle Additional Components (Priority: Low)
1. **Decide on geocoding.py:**
   - Currently in `core/algorithms/geocoding.py`
   - Options:
     - Move to `utils/geocoding.py` (utility function)
     - Keep in core if it's a core algorithm

2. **Weather subsystem decision:**
   - Current `core/weather/` has good separation
   - Options:
     - Keep as subsystem but move interfaces
     - Or flatten completely per original plan

## Proposed Final Structure

```
better-lbnl/
├── src/
│   └── better_lbnl/
│       ├── core/                  # Core algorithms and domain logic
│       │   ├── __init__.py
│       │   ├── changepoint.py     # Change-point model fitting
│       │   ├── benchmarking.py    # Statistical benchmarking
│       │   ├── savings.py         # Savings estimation
│       │   ├── recommendations.py # EE measure recommendations
│       │   └── weather/           # Complete weather subsystem
│       │       ├── __init__.py
│       │       ├── calculations.py # HDD/CDD, temp conversions (from weather.py)
│       │       ├── providers.py    # OpenMeteo, NOAA implementations
│       │       └── service.py      # Weather service orchestration
│       ├── data/                  # Data structures and domain models
│       │   ├── __init__.py
│       │   ├── models.py          # Domain models with behavior
│       │   ├── services.py        # Service layer (orchestration)
│       │   ├── constants.py       # Physical constants
│       │   └── validators.py      # Input validation
│       ├── utils/                 # General-purpose utility functions
│       │   ├── __init__.py
│       │   ├── unit_conversion.py # Non-weather unit conversions
│       │   ├── statistics.py      # Statistical utilities
│       │   ├── geography.py       # Geographic utilities
│       │   └── geocoding.py       # Geocoding utilities
│       └── interfaces/            # Abstract interfaces (ports)
│           ├── __init__.py
│           ├── weather_source.py  # Weather data source interface
│           ├── benchmark_source.py # Benchmark data interface
│           └── measure_database.py # Measure database interface
```

### Key Clarification: Weather Module Organization

**Why weather is only in `core/` and not in `utils/`:**
- Weather is a **core domain** for building energy analysis, not a utility
- All weather-related functionality stays together in `core/weather/`
- The `calculations.py` file contains what was previously in `core/algorithms/weather.py`
- `utils/` contains only general-purpose utilities that aren't domain-specific

### Subsystem Pattern for Core Modules

This subsystem pattern can be applied to ANY core module as it grows:

#### Current State (Simple Modules):
```
core/
├── changepoint.py         # Single file is sufficient
├── benchmarking.py        # Single file is sufficient
└── weather/               # Already a subsystem
    ├── calculations.py
    ├── providers.py
    └── service.py
```

#### Future State (As Modules Grow):
```
core/
├── changepoint/           # Can become a subsystem
│   ├── __init__.py
│   ├── models.py         # Different model types (3P, 5P, etc.)
│   ├── fitting.py        # Fitting algorithms
│   ├── validation.py     # Model validation
│   └── visualization.py  # Plotting functions
├── benchmarking/          # Can become a subsystem
│   ├── __init__.py
│   ├── calculations.py   # Z-score, percentiles
│   ├── providers.py      # ENERGY STAR, CBECS, etc.
│   ├── ratings.py        # Rating assignments
│   └── reports.py        # Benchmark report generation
├── savings/               # Can become a subsystem
│   ├── __init__.py
│   ├── estimation.py     # Core estimation logic
│   ├── baselines.py      # Baseline calculations
│   ├── adjustments.py    # Weather normalization
│   └── uncertainty.py    # Confidence intervals
└── weather/               # Already a subsystem
    └── ...
```

#### When to Convert to a Subsystem:
1. **Multiple related functions** (>3-4 functions)
2. **Different aspects** (providers, calculations, services)
3. **External integrations** (multiple data sources)
4. **Complex domain logic** requiring separation

#### Benefits:
- **Start simple** - Single file until complexity demands more
- **Scale naturally** - Convert to subsystem when needed
- **Consistent pattern** - All subsystems follow same structure
- **No premature optimization** - Only create structure when necessary

## Migration Steps

### Step-by-Step Commands

```bash
# Phase 1: Core restructuring
mv src/better_lbnl/core/algorithms/changepoint.py src/better_lbnl/core/
mv src/better_lbnl/core/algorithms/weather.py src/better_lbnl/core/weather/calculations.py
mv src/better_lbnl/core/algorithms/statistics.py src/better_lbnl/utils/
mv src/better_lbnl/core/algorithms/geocoding.py src/better_lbnl/utils/
rm -rf src/better_lbnl/core/algorithms/

# Phase 2: Data/Domain consolidation
mv src/better_lbnl/domain/models.py src/better_lbnl/data/
mv src/better_lbnl/domain/services.py src/better_lbnl/data/
rmdir src/better_lbnl/domain/

# Phase 3: Interfaces
mv src/better_lbnl/core/weather/interfaces.py src/better_lbnl/interfaces/weather_source.py
```

### Import Updates Required

After reorganization, update all imports:

1. **From:** `from better_lbnl.core.algorithms.changepoint import ...`  
   **To:** `from better_lbnl.core.changepoint import ...`

2. **From:** `from better_lbnl.domain.models import ...`  
   **To:** `from better_lbnl.data.models import ...`

3. **From:** `from better_lbnl.core.algorithms.weather import ...`  
   **To:** `from better_lbnl.utils.weather import ...`

4. **From:** `from better_lbnl.core.weather.interfaces import ...`  
   **To:** `from better_lbnl.interfaces.weather_source import ...`

## Benefits of Reorganization

1. **Clearer Separation of Concerns:**
   - Core: Pure algorithms
   - Data: Models and orchestration
   - Utils: Helper functions
   - Interfaces: Contracts

2. **Flatter Structure:**
   - Reduces nesting depth
   - Easier imports
   - Better discoverability

3. **Alignment with Original Vision:**
   - Follows the workplan architecture
   - Consistent with documentation

4. **Hybrid Approach Preserved:**
   - Keeps valuable additions (services, geography)
   - Maintains domain model pattern

## Risks and Mitigation

### Risks:
1. Breaking existing code/tests
2. Import path changes
3. Git history fragmentation

### Mitigation:
1. Run tests after each phase
2. Use automated refactoring tools
3. Create git commit for each phase
4. Keep backward compatibility aliases temporarily

## Recommendation

**Proceed with reorganization** but in phases:

1. **Phase 1-2 immediately** (High priority, core structure)
2. **Phase 3-4 next sprint** (Medium priority, utilities)
3. **Phase 5 as needed** (Low priority, cleanup)

This maintains the hybrid architecture benefits while aligning with the original plan.