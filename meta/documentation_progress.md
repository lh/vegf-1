# Documentation Progress

## Current Status (May 3, 2025)

We are improving documentation across the project using numpy-style docstrings to support Sphinx documentation generation.

### Recent Documentation Updates

1. **run_simulation.py**
   - Updated module docstring to include command-line argument documentation
   - Added detailed example usage section
   - Added proper NumPy-style docstrings for all functions
   - Added documentation for the new command-line argument handling

2. **eylea_literature_based.yaml**
   - Updated configuration file with proper structure
   - Added comments explaining parameter values and sources
   - Ensured compatibility with the updated configuration parser

3. **simulation/config.py**
   - Fixed all docstring formatting issues
   - Added Parameters and Returns sections to all method docstrings
   - Added documentation for sensitivity analysis parameters
   - Added documentation for cost parameters
   - Added documentation for treatment discontinuation parameters

### Documentation Standards

All documentation should follow numpy-style docstring format with these sections:

```python
"""Short description.

Extended description with details about functionality.

Parameters
----------
param1 : type
    Description of param1
param2 : type
    Description of param2

Returns
-------
type
    Description of return value

Raises
------
ErrorType
    When bad things happen

Examples
--------
>>> example_code()
result
"""
```

### Documentation Structure

We follow a specific structure for our Sphinx documentation:

1. **Index Files**: Keep index.rst files brief and use them as tables of contents
   - Use toctree directives to list module pages
   - Do NOT include automodule directives in index files
   - Example: docs/simulation/index.rst lists simulation modules but doesn't document them directly

2. **Module Files**: Create individual .rst files for each module
   - Use automodule directives in these files
   - Include members, undoc-members, and show-inheritance options
   - Example: docs/simulation/config.rst documents the simulation.config module

3. **Avoiding Duplicate Documentation**:
   - Never document the same module in multiple places
   - Do not use :no-index: in Python docstrings
   - Use cross-references instead of duplicating documentation

For detailed guidelines, see meta/documentation_guidelines.md.

### Next Files to Document

1. Test files (see meta/documentation_errors.log for the full list)
2. Remaining formatting issues in:
   - simulation/config.py
   - simulation/scheduler.py
   - simulation/patient_state.py
   - simulation/clinical_model.py

### Validation

Use the docgen MCP server to validate docstrings:
```python
{
  "module_path": "path/to/module.py",
  "strict_validation": true
}
```

## Documentation Checklist

### Core Files
- [x] protocol_models.py
- [x] protocols/config_parser.py  
- [x] simulation/clinical_model.py
- [x] simulation/patient_state.py
- [x] protocols/visit_types.yaml
- [x] validation/config_validator.py
- [x] visualization/outcome_viz.py
- [x] simulation/config.py
- [x] simulation/scheduler.py
- [x] simulation/base.py
- [x] simulation/abs.py
- [x] simulation/des.py

### Configuration Files
- [x] conftest.py
- [x] docs/conf.py
- [x] setup_env.py
- [x] protocols/simulation_configs/eylea_literature_based.yaml

### Protocol Files  
- [x] protocols/__init__.py
- [x] protocol_parameters.py
- [x] protocol_parser.py

### Test Files
- [ ] test_des_simulation.py
- [ ] test_abs_simulation.py
- [ ] test_des_queues.py
- [ ] test_multiple_simulations.py
- [ ] test_protocol_configs.py
- [ ] test_protocol_config_validation.py
- [ ] test_protocol_models.py
- [ ] tests/unit/test_abs_patient_generator.py
- [ ] tests/unit/test_population_viz.py
- [ ] tests/unit/test_clinical_model.py
- [ ] tests/unit/test_agent_state.py
- [ ] tests/unit/test_clinical_model_v2.py
- [ ] tests/unit/test_simulation_events.py
- [ ] tests/unit/test_simulation_results.py
- [ ] tests/unit/test_simulation_base.py

### Scripts
- [x] run_simulation.py
- [x] run_eylea_analysis.py

## Notes

- Focus on documenting public interfaces first
- Include examples for complex functionality
- Document parameter types and return values
- Update this file when documentation is completed for a file
