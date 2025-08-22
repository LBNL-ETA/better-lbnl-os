# VS Code Testing Configuration

This directory contains VS Code configuration files to enable seamless testing in the IDE.

## Files

- **`settings.json`**: Main VS Code settings for Python and testing configuration
- **`launch.json`**: Debug configurations for running and debugging tests
- **`tasks.json`**: Task definitions for running tests from the command palette
- **`README.md`**: This file with usage instructions

## How to Use VS Code Testing

### 1. Test Discovery

VS Code should automatically discover tests when you open the project. You can:

- Open the **Testing** tab in the sidebar (test tube icon)
- Tests are organized by file and test class
- All 98+ tests should be visible in the test explorer

### 2. Running Tests

**From the Testing Tab:**
- Click the play button next to individual tests, test classes, or test files
- Right-click on tests for more options (run, debug, etc.)
- Use the "Run All Tests" button at the top

**From Command Palette (Ctrl+Shift+P):**
- `Python: Run All Tests`
- `Python: Run Current Test File`
- `Tasks: Run Task` → Select test task

**From Keyboard Shortcuts:**
- `Ctrl+;` followed by `A` - Run all tests
- `Ctrl+;` followed by `F` - Run tests in current file
- `Ctrl+;` followed by `C` - Run test at cursor

### 3. Debugging Tests

**From the Testing Tab:**
- Right-click on a test and select "Debug Test"
- Set breakpoints in your test files or source code

**From Run and Debug Tab:**
- Select "Python: Debug Tests" configuration
- Select "Python: Debug Current Test File" for the active file

### 4. Test Configuration

The tests are configured to:
- Use the UV-managed virtual environment (`.venv`)
- Run without coverage by default (faster)
- Include verbose output (`-v` flag)
- Use the correct Python path for imports

### 5. Available Tasks

From Command Palette → `Tasks: Run Task`:

- **Run All Tests**: Runs all tests without coverage
- **Run Tests with Coverage**: Runs all tests with coverage report
- **Run Unit Tests Only**: Runs only unit tests (faster)

## Troubleshooting

### Tests Not Discovered

1. Ensure the Python interpreter is set to `.venv/Scripts/python.exe`
2. Check that `PYTHONPATH` includes the `src` directory
3. Reload the window: `Ctrl+Shift+P` → "Developer: Reload Window"

### Import Errors

1. Verify the virtual environment is activated
2. Check that all dependencies are installed: `uv sync`
3. Ensure `src` is in the Python path

### Performance Issues

- Use "Run Unit Tests Only" for faster testing
- Disable coverage for development testing
- Run specific test files instead of all tests

## Project Structure

```
better-lbnl-os/
├── .vscode/              # VS Code configuration
├── src/better_lbnl/      # Source code
├── tests/                # Test files
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test fixtures
└── .venv/               # Virtual environment
```

## Test Categories

- **Unit Tests** (`tests/unit/`): Fast, isolated tests
- **Integration Tests** (`tests/integration/`): Tests with external dependencies
- **Weather Tests** (`tests/test_weather*.py`): Weather-related functionality

Total: 98+ tests covering models, algorithms, and services.
