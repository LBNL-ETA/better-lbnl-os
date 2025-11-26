Getting Started
===============

Installation
------------

Using pip
^^^^^^^^^

.. code-block:: bash

    pip install better-lbnl-os

Using uv (recommended)
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    uv add better-lbnl-os

Development Installation
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    git clone https://github.com/LBNL-ETA/better-lbnl-os.git
    cd better-lbnl-os
    uv venv
    uv pip install -e ".[dev]"

Quick Start
-----------

Here's a simple example that fits a change-point model to building energy data:

.. code-block:: python

    from better_lbnl_os import fit_changepoint_model
    import numpy as np

    # Prepare temperature and energy data (showing heating and cooling patterns)
    temperatures = np.array([30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85])  # degF
    energy_use = np.array([150, 140, 125, 110, 95, 85, 80, 80, 85, 95, 110, 125])  # kBtu/day

    # Fit change-point model
    model_result = fit_changepoint_model(temperatures, energy_use)

    # Check model quality
    if model_result.is_valid():
        print(f"Model Type: {model_result.model_type}")  # 5P (heating and cooling)
        print(f"R-squared: {model_result.r_squared:.3f}")  # 0.995
        print(f"Baseload: {model_result.baseload:.1f}")  # 80.0

Basic Concepts
--------------

Change-Point Models
^^^^^^^^^^^^^^^^^^^

BETTER uses change-point regression models to characterize building energy consumption
as a function of outdoor air temperature. The library supports three model types:

- **1P (One Parameter)**: Constant energy use, no temperature dependence
- **3P (Three Parameter)**: Linear relationship with a single change-point (heating-only or cooling-only)
- **5P (Five Parameter)**: Two change-points with heating slope, cooling slope, and baseload

The model fitting algorithm automatically selects the best model type based on the data.

Workflow Overview
^^^^^^^^^^^^^^^^^

A typical analysis workflow involves:

1. **Data Preparation**: Load building metadata and utility bills
2. **Weather Alignment**: Match energy data with outdoor temperature data
3. **Model Fitting**: Fit change-point models to characterize energy use
4. **Benchmarking**: Compare building performance against peers
5. **Recommendations**: Identify energy efficiency improvement opportunities
6. **Savings Estimation**: Quantify potential energy and cost savings

Next Steps
----------

- See the :doc:`user_guide` for detailed explanations of each feature
- Explore the :doc:`examples` for working code samples
- Check the API reference for detailed function documentation
