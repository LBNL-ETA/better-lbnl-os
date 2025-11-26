User Guide
==========

Overview
--------

BETTER-LBNL-OS is the open-source analytical engine underlying the
`BETTER web application <https://better.lbl.gov>`_ (Building Efficiency Targeting
Tool for Energy Retrofits). It provides Python APIs for:

- Change-point model fitting for building energy analysis
- Statistical benchmarking against peer buildings
- Energy efficiency measure recommendations
- Savings estimation with uncertainty quantification

This guide walks through the main features and workflows.

Data Models
-----------

Building Data
^^^^^^^^^^^^^

The :class:`~better_lbnl_os.BuildingData` class represents a building with its metadata:

.. code-block:: python

    from better_lbnl_os import BuildingData

    building = BuildingData(
        name="Office Building",
        floor_area=5000,  # square meters
        space_type="Office",
        location="Berkeley, CA"
    )

Utility Bills
^^^^^^^^^^^^^

The :class:`~better_lbnl_os.UtilityBillData` class represents utility bill records:

.. code-block:: python

    from better_lbnl_os import UtilityBillData
    from datetime import date

    bill = UtilityBillData(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 31),
        consumption=1500,  # kWh
        fuel_type="electricity",
        cost=150.00
    )

Change-Point Model Fitting
--------------------------

The core analytical capability is fitting change-point regression models that
characterize building energy consumption as a function of outdoor temperature.

Basic Model Fitting
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from better_lbnl_os import fit_changepoint_model
    import numpy as np

    # Temperature data (degF)
    temperatures = np.array([30, 40, 50, 60, 70, 80, 90])

    # Energy consumption (kBtu/day)
    energy = np.array([120, 100, 85, 75, 80, 95, 115])

    result = fit_changepoint_model(temperatures, energy)

    print(f"Model type: {result.model_type}")
    print(f"R-squared: {result.r_squared:.3f}")
    print(f"CV(RMSE): {result.cvrmse:.1f}%")

Model Types
^^^^^^^^^^^

The library automatically selects the best model from:

**1P Model (One Parameter)**
    Constant energy use with no temperature dependence. Suitable for
    process-dominated loads.

**3P Model (Three Parameter)**
    Linear relationship with a single change-point temperature. Used for
    heating-only or cooling-only buildings.

    - 3P Heating: Energy increases below the change-point
    - 3P Cooling: Energy increases above the change-point

**5P Model (Five Parameter)**
    Two change-points defining heating and cooling regions with a
    temperature-independent baseload between them. Common for buildings
    with both heating and cooling systems.

Model Quality Metrics
^^^^^^^^^^^^^^^^^^^^^

- **R-squared (R2)**: Coefficient of determination (0-1, higher is better)
- **CV(RMSE)**: Coefficient of variation of root mean square error (lower is better)

.. code-block:: python

    from better_lbnl_os import calculate_r_squared, calculate_cvrmse

    r2 = calculate_r_squared(actual, predicted)
    cvrmse = calculate_cvrmse(actual, predicted)

Benchmarking
------------

Compare building performance against reference statistics or peer groups.

Using Reference Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from better_lbnl_os import (
        benchmark_building,
        get_reference_statistics,
        list_available_reference_statistics
    )

    # See available reference datasets
    available = list_available_reference_statistics()
    print(available)

    # Get reference statistics for a space type
    ref_stats = get_reference_statistics("office")

    # Benchmark a building's model against reference
    benchmark_result = benchmark_building(model_result, ref_stats)

    print(f"Percentile rank: {benchmark_result.percentile:.1f}")

Creating Custom Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^

Build reference statistics from your own portfolio:

.. code-block:: python

    from better_lbnl_os import create_statistics_from_models

    # List of ChangePointModelResult objects from your buildings
    models = [model1, model2, model3, ...]

    custom_stats = create_statistics_from_models(models)

Energy Efficiency Recommendations
---------------------------------

Detect inefficiency symptoms and generate measure recommendations:

.. code-block:: python

    from better_lbnl_os import detect_symptoms, recommend_ee_measures

    # Detect symptoms from benchmark results
    symptoms = detect_symptoms(benchmark_result)

    for symptom in symptoms:
        print(f"- {symptom.description}")

    # Get measure recommendations
    recommendations = recommend_ee_measures(symptoms)

    for rec in recommendations.measures:
        print(f"- {rec.measure_name}: {rec.description}")

Available Measures
^^^^^^^^^^^^^^^^^^

The library includes recommendations for common energy efficiency measures:

- Lighting upgrades
- HVAC optimization
- Building envelope improvements
- Controls and scheduling
- Equipment efficiency upgrades

Savings Estimation
------------------

Estimate potential energy and cost savings:

.. code-block:: python

    from better_lbnl_os import estimate_savings

    savings = estimate_savings(
        model_result=model_result,
        benchmark_result=benchmark_result,
        fuel_type="electricity",
        energy_rate=0.12  # $/kWh
    )

    print(f"Annual energy savings: {savings.energy_savings:.0f} kWh")
    print(f"Annual cost savings: ${savings.cost_savings:.2f}")

Pipeline Helpers
----------------

For end-to-end workflows, the library provides convenience functions:

.. code-block:: python

    from better_lbnl_os import (
        fit_models_with_auto_weather,
        resolve_location
    )

    # Resolve location to get coordinates
    location = resolve_location("Berkeley, CA")

    # Fit models with automatic weather data fetching
    results = fit_models_with_auto_weather(
        bills=utility_bills,
        location=location
    )

Services
--------

For complex workflows, use the service classes:

.. code-block:: python

    from better_lbnl_os import BuildingAnalyticsService

    service = BuildingAnalyticsService()

    # Run complete analysis
    analysis = service.analyze(building_data, utility_bills)
