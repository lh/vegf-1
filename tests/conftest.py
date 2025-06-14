"""Pytest configuration file for the ophthalmic treatment simulation project.

This file provides test configuration and fixtures that are automatically
available to all tests in the project. It runs before any tests are collected.

Key Features
------------
- Adds project root to Python path for test imports
- Provides common test fixtures
- Configures test environment

Fixtures
-------
None currently defined, but available for future test fixtures

Usage Notes
----------
- This file must remain in the project root directory
- Pytest automatically detects and uses this configuration
- Changes here affect all tests in the project

Examples
--------
To run tests with this configuration:
```bash
pytest tests/
```

To see available fixtures:
```bash
pytest --fixtures
```

See Also
--------
- pytest documentation: https://docs.pytest.org/
- Python path documentation: https://docs.python.org/3/library/sys.html#sys.path
"""

import os
import sys

# Add project root to Python path for test imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
