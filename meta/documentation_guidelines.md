# Documentation Guidelines

This document outlines the standard approach for documenting code and structuring Sphinx documentation in this project.

## Python Docstrings

All Python code should use NumPy-style docstrings. This format is well-supported by Sphinx and provides a clear structure for documenting parameters, return values, and examples.

### Example Docstring Format

```python
def function_name(param1, param2):
    """Short description of function.

    More detailed description that explains what the function does,
    its purpose, and any important details.

    Parameters
    ----------
    param1 : type
        Description of param1
    param2 : type
        Description of param2

    Returns
    -------
    return_type
        Description of return value

    Raises
    ------
    ExceptionType
        When/why this exception is raised

    Examples
    --------
    >>> function_name(1, 2)
    3

    Notes
    -----
    Additional notes and implementation details.
    """
```

### Important Formatting Rules

1. Always include a blank line after the one-line summary
2. Always include a blank line after parameter lists, return sections, etc.
3. Use proper indentation for multi-line descriptions
4. Include examples where appropriate
5. Document all parameters and return values

## Sphinx Documentation Structure

To avoid duplicate documentation warnings and maintain a clean structure, we follow these guidelines:

### Module Documentation Structure

1. **Index Files**: Use index.rst files as tables of contents, not for documenting modules directly
   - Example: `docs/simulation/index.rst` should use `toctree` to list module pages
   - Do NOT use `automodule` directives in index files

2. **Module Pages**: Create individual .rst files for each module
   - Example: `docs/simulation/config.rst` for the `simulation.config` module
   - Use `automodule` directives in these files

### Example Index File (simulation/index.rst)

```rst
Simulation Modules
=================

This section contains documentation for the simulation modules.

.. toctree::
   :maxdepth: 2
   
   base
   patient_state
   scheduler
   config
   clinical_model
```

### Example Module File (simulation/config.rst)

```rst
Simulation Config Module
=======================

.. automodule:: simulation.config
   :members:
   :undoc-members:
   :show-inheritance:
```

### Avoiding Duplicate Documentation

- Never document the same module in multiple places
- Do not use `:no-index:` in Python docstrings - this should only be used in RST files if needed
- If you need to reference a module in multiple places, use cross-references instead of duplicating documentation

## Building Documentation

To build the documentation:

```bash
cd docs
make html
```

Check for warnings in the build output and fix them before committing changes.
