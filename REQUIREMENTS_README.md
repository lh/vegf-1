# Requirements Management

This project has been cleaned up to use a simple two-file requirements structure:

## Installation

### For Users (Production)
```bash
pip install -r requirements.txt
```

### For Developers
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

## Requirements Files

### requirements.txt
Contains only the core dependencies needed to run the simulation and Streamlit app:
- Scientific computing: numpy, pandas, scipy, scikit-learn
- Visualization: matplotlib, seaborn, plotly, altair
- Web framework: streamlit
- Agent-based modeling: Mesa
- Data storage: pyarrow, polars
- Utilities: PyYAML, tqdm, click, etc.

### requirements-dev.txt
Contains additional tools for development:
- Testing: pytest and plugins
- Code quality: black, flake8, mypy, pylint
- Documentation: sphinx and themes
- Jupyter notebooks
- Browser automation: playwright
- Debugging and profiling tools

## Version Strategy

- Uses minimum version constraints with upper bounds for major versions
- This prevents breaking changes while allowing patch and minor updates
- Example: `numpy>=1.24.0,<2.0.0`

## Python Version

Requires Python 3.9 or higher.

## Notes

- The old requirements_minimal.txt, streamlit_requirements.txt, and requirements-sphinx.txt have been removed
- All dependencies are now consolidated into the two main files
- No conda-specific entries - all packages are pip-installable