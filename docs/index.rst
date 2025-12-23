.. BETTER-LBNL-OS documentation master file

BETTER-LBNL-OS Documentation
============================

.. image:: https://img.shields.io/pypi/v/better-lbnl-os.svg
   :target: https://pypi.org/project/better-lbnl-os/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/better-lbnl-os.svg
   :target: https://pypi.org/project/better-lbnl-os/
   :alt: Python versions

.. image:: https://github.com/LBNL-ETA/better-lbnl/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/LBNL-ETA/better-lbnl/actions
   :alt: CI status

Welcome to BETTER-LBNL-OS, an open-source Python library for building energy analytics extracted from the `Building Efficiency Targeting Tool for Energy Retrofits (BETTER) <https://better.lbl.gov>`_. BETTER is a software toolkit that enables building operators to quickly, easily identify the most cost-saving energy efficiency measures in buildings and portfolios. BETTER is made possible by support from the U.S. Department of Energy (DOE) Building Technologies Office (BTO).

Features
--------

- **Change-point Model Fitting**: Automated fitting of 1-, 3-, 5-parameter (1P/3P/5P) models
- **Building Benchmarking**: Statistical performance comparison of building energy performance against peer groups
- **Energy Savings Estimation**: Weather-normalized energy savings calculations with uncertainty quantification
- **Energy Efficiency Recommendations**: Rule-based recommendations for energy efficiency improvements
- **Portfolio Analytics**: Aggregate analysis across multiple buildings

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

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
