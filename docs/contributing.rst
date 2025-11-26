Contributing
============

We welcome contributions to BETTER-LBNL-OS! This guide will help you get started.

Development Setup
-----------------

1. Fork the repository on GitHub

2. Clone your fork:

   .. code-block:: bash

       git clone https://github.com/YOUR-USERNAME/better-lbnl-os.git
       cd better-lbnl-os

3. Create a virtual environment and install dependencies:

   .. code-block:: bash

       uv venv
       uv pip install -e ".[dev]"

4. Create a feature branch:

   .. code-block:: bash

       git checkout -b feature/amazing-feature

Running Tests
-------------

Run the full test suite:

.. code-block:: bash

    pytest

Run with coverage report:

.. code-block:: bash

    pytest --cov=better_lbnl_os --cov-report=html

Run specific test categories:

.. code-block:: bash

    pytest -m "not slow"    # Skip slow tests
    pytest tests/unit/      # Only unit tests

Code Style
----------

This project uses the following tools for code quality:

**Ruff** - Linting and import sorting:

.. code-block:: bash

    ruff check .
    ruff check . --fix  # Auto-fix issues

**Black** - Code formatting:

.. code-block:: bash

    black .

**Mypy** - Type checking:

.. code-block:: bash

    mypy src

Run all checks before committing:

.. code-block:: bash

    ruff check . && black . && mypy src

Pre-commit Hooks
----------------

We recommend setting up pre-commit hooks:

.. code-block:: bash

    pre-commit install

This will automatically run linting and formatting checks before each commit.

Submitting Changes
------------------

1. Make your changes and ensure all tests pass
2. Run the linting and formatting checks
3. Commit your changes with a clear commit message:

   .. code-block:: bash

       git commit -m "Add amazing feature"

4. Push to your fork:

   .. code-block:: bash

       git push origin feature/amazing-feature

5. Open a Pull Request on GitHub

Pull Request Guidelines
-----------------------

- Include a clear description of the changes
- Add tests for new functionality
- Update documentation as needed
- Ensure all CI checks pass
- Keep commits focused and atomic

Reporting Issues
----------------

Found a bug or have a feature request? Please open an issue on GitHub:

https://github.com/LBNL-ETA/better-lbnl-os/issues

Include:

- A clear description of the issue
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Python version and OS
- Relevant code snippets or error messages
