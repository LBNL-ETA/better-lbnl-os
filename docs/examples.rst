Examples
========

The ``examples/`` directory contains working code samples demonstrating various
use cases for the BETTER-LBNL library.

Benchmarking Demo
-----------------

**File:** ``examples/benchmarking_demo.py``

Demonstrates the complete benchmarking workflow including:

- Loading building data
- Fitting change-point models
- Benchmarking against reference statistics
- Generating efficiency recommendations

Interactive Notebook
--------------------

**File:** ``examples/notebooks/explore.ipynb``

A Jupyter notebook for interactive exploration of the library's features.
Useful for learning and experimentation.

Weather Data Examples
---------------------

The ``examples/weather/`` directory contains examples for working with weather data:

**simple_weather_example.py**
    Basic example of fetching weather data for a location.

**get_weather_data.py**
    More comprehensive weather data retrieval with multiple providers.

**weather_for_energy_analysis.py**
    Demonstrates aligning weather data with utility bill periods for
    energy analysis.

Running the Examples
--------------------

1. Install the package with development dependencies:

   .. code-block:: bash

       uv pip install -e ".[dev,examples]"

2. Run a Python example:

   .. code-block:: bash

       python examples/benchmarking_demo.py

3. Or start Jupyter for the notebook:

   .. code-block:: bash

       jupyter notebook examples/notebooks/explore.ipynb
