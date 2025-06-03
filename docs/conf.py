"""Sphinx documentation configuration for the Macular Simulation project.

This file configures how Sphinx generates documentation from the project's
source code and documentation files. It enables automatic API documentation
generation from docstrings and configures the documentation output format.

Key Features
------------
- Automatic API documentation from numpy-style docstrings
- ReadTheDocs theme integration
- Type hint support in documentation
- Custom documentation sections and organization

Configuration Sections
---------------------
1. Project Information: Basic metadata about the project
2. General Configuration: Core Sphinx settings and extensions
3. Napoleon Settings: Numpy docstring parsing configuration
4. HTML Output: Theme and static file configuration
5. Autodoc Settings: API documentation generation options

Extensions
----------
- sphinx.ext.autodoc: Generates API docs from docstrings
- sphinx.ext.napoleon: Supports numpy-style docstrings
- sphinx.ext.viewcode: Links to source code
- sphinx_rtd_theme: ReadTheDocs theme
- sphinx_autodoc_typehints: Better type hint rendering

Usage Notes
----------
- Documentation is built using `make html` in docs directory
- Requires all docstrings to follow numpy format
- Type hints are automatically included in docs
- Private members (starting with _) are excluded by default

Examples
--------
To build documentation locally:
```bash
cd docs
make html
```

The documentation will be generated in docs/_build/html.

See Also
--------
- Sphinx documentation: https://www.sphinx-doc.org/
- Napoleon extension: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
- ReadTheDocs theme: https://sphinx-rtd-theme.readthedocs.io/
"""

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Macular Simulation'
copyright = '2025, Luke Herbert'
author = 'Luke Herbert'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# Import Mozilla theme
import mozilla_sphinx_theme

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
    'myst_parser'
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Napoleon settings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

# MyST Parser settings
myst_enable_extensions = [
    "amsmath",          # For LaTeX math
    "colon_fence",      # For code blocks with colons
    "deflist",          # For definition lists
    "dollarmath",       # For inline math with $
    "html_admonition",  # For HTML-style admonitions
    "html_image",       # For HTML-style images
    "linkify",          # For auto-linking URLs
    "replacements",     # For text replacements
    "smartquotes",      # For smart quotes
    "substitution",     # For variable substitution
    "tasklist",         # For task lists
]
myst_heading_anchors = 3  # Generate anchors for h1-h3
myst_update_mathjax = False  # Don't update MathJax

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'mozilla'
html_theme_path = [os.path.dirname(mozilla_sphinx_theme.__file__)]
html_static_path = ['_static']

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
autodoc_typehints = 'description'
