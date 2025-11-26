.. BETTER-LBNL documentation master file

BETTER-LBNL Documentation
=========================

.. image:: https://img.shields.io/pypi/v/better-lbnl-os.svg
   :target: https://pypi.org/project/better-lbnl-os/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/better-lbnl-os.svg
   :target: https://pypi.org/project/better-lbnl-os/
   :alt: Python versions

.. image:: https://github.com/LBNL-ETA/better-lbnl/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/LBNL-ETA/better-lbnl/actions
   :alt: CI status

Welcome to BETTER-LBNL, an open-source Python library for building energy analytics extracted from 
the BETTER (Building Efficiency Targeting Tool for Energy Retrofits) platform.

Features
--------

- **Change-point Model Fitting**: Automated fitting of 1P, 3P, and 5P models
- **Building Benchmarking**: Statistical performance comparison
- **Savings Estimation**: Weather-normalized energy savings calculations
- **EE Recommendations**: Energy efficiency measure suggestions
- **Portfolio Analytics**: Multi-building aggregate analysis

Quick Start
-----------

Installation::

    pip install better-lbnl-os

Basic usage::

    from better_lbnl_os import BuildingData, fit_changepoint_model
    import numpy as np

    # Create a building
    building = BuildingData(
        name="Office Building",
        floor_area=50000,
        space_type="Office",
        location="Berkeley, CA"
    )

    # Fit change-point model
    temperatures = np.array([45, 50, 55, 60, 65, 70, 75, 80])
    energy_use = np.array([120, 110, 95, 85, 80, 82, 95, 115])
    
    model = fit_changepoint_model(temperatures, energy_use)
    print(f"R-squared: {model.r_squared:.3f}")

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   user_guide
   examples
   contributing
   changelog

.. toctree::
   :maxdepth: 1
   :caption: API Reference:

   api/models
   api/changepoint
   api/benchmarking
   api/recommendations
   api/savings
   api/pipeline

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
