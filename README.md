# APE: AMD Protocol Explorer

This repository contains the codebase for simulating, analyzing, and visualizing AMD treatment protocols, with a focus on VEGF inhibitors like Eylea. The project includes tools for modeling disease progression, analyzing treatment outcomes, and visualizing results through both command line tools and an interactive Streamlit dashboard.

## Features

- **Simulation Models**: Agent-based and discrete event simulations for disease progression and treatment effects.
- **Parameter Configurations**: YAML-based configuration files for flexible protocol definitions.
- **Data Analysis**: Tools for analyzing injection intervals, visual acuity changes, and treatment persistence.
- **Visualization**: Generate heatmaps, waterfall plots, and other visualizations for treatment patterns with a consistent Tufte-inspired visual grammar.
- **Interactive Dashboard**: Streamlit-based interface for running simulations and exploring results.
- **Report Generation**: Create comprehensive reports with Quarto integration.

## Documentation

Comprehensive documentation for the project is available. To view it, click the link below:

[View Documentation](https://lh.github.io/vegf-1/)


The documentation includes:
- Setup instructions
- Detailed descriptions of simulation models
- Examples of configuration files
- Analysis and visualization guides

## Repository Structure

```
├── protocols/                # Configuration files for simulations
│   ├── parameter_sets/       # Parameter sets for different protocols
│   └── simulation_configs/   # Simulation configuration files
├── simulation/               # Core simulation models and logic
├── validation/               # Configuration validation tools
├── visualization/            # Visualization scripts and templates
│   ├── color_system.py      # Centralized color palette
│   ├── visualization_templates.py  # Standardized chart templates
│   └── acuity_viz.py        # Visual acuity visualization functions
├── streamlit_app/            # Interactive Streamlit dashboard
│   ├── app.py                # Main Streamlit application
│   ├── amd_protocol_explorer.py  # Dashboard implementation
│   ├── simulation_runner.py  # Simulation execution
│   ├── quarto_utils.py       # Quarto integration
│   ├── assets/               # Dashboard assets
│   └── reports/              # Quarto report templates
├── tests/                    # Unit tests for the project
├── docs/                     # Sphinx documentation source
├── run_ape.py                # Entry point for the Streamlit app
└── setup_streamlit.py        # Setup script for the Streamlit environment
```

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ape.git
   cd ape
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run a sample simulation from the command line:
   ```bash
   python run_eylea_analysis.py --config protocols/simulation_configs/test_simulation.yaml --output output/
   ```

4. View the results in the `output/` directory.

### Running the Dashboard

1. Install Streamlit dependencies:
   ```bash
   pip install -r streamlit_requirements.txt
   ```

2. Setup the Streamlit environment:
   ```bash
   python setup_streamlit.py
   ```

3. Run the dashboard:
   ```bash
   python run_ape.py
   ```

4. Access the dashboard in your browser at http://localhost:8502

## Visualization System

The project includes a comprehensive visualization system that follows Edward Tufte's design principles:

1. **Consistent Color System**:
   - Steel Blue (`#4682B4`) for visual acuity data
   - Sage Green (`#8FAD91`) for patient counts
   - Firebrick Red (`#B22222`) for critical information

2. **Standardized Templates**:
   - `patient_time` - Visual acuity by patient time with sample counts
   - `enrollment_chart` - Patient enrollment over time
   - `acuity_time_series` - Visual acuity time series
   - `protocol_comparison` - Treatment protocol comparison

3. **Usage**:
   ```python
   from visualization.visualization_templates import create_patient_time_visualization

   fig, ax = create_patient_time_visualization(
       data,
       time_col='weeks_since_enrollment',
       acuity_col='etdrs_letters',
       title='Visual Acuity Over Time'
   )
   ```

For more details, see the [Visualization README](visualization/README.md).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
