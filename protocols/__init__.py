"""Protocol definitions and configuration for macular simulation.

This package contains all protocol-related functionality including:
- Protocol definitions (YAML files)
- Protocol parsing and validation
- Protocol parameter management
- Visit type definitions

Key Modules
-----------
- config_parser.py: Load and parse protocol configuration files
- visit_types.yaml: Definitions of visit types and their properties
- parameter_sets/: Protocol parameter configurations
- protocol_definitions/: Protocol definition files

Usage
-----
Import protocol configurations:
```python
from protocols import config_parser
from protocols.visit_types import load_visit_types
```

Load a protocol:
```python
protocol = config_parser.load_protocol('eylea.yaml')
```

See Also
--------
- protocol_models.py: Protocol data models
- validation/config_validator.py: Protocol validation
- simulation/clinical_model.py: Protocol execution
"""

# Package version
__version__ = '1.0.0'
