# VEGF-1: Ophthalmic Treatment Protocol Simulations

This repository contains the codebase for simulating and analyzing ophthalmic treatment protocols, with a focus on VEGF inhibitors like Eylea. The project includes tools for modeling disease progression, analyzing treatment outcomes, and visualizing results.

## Features

- **Simulation Models**: Agent-based simulations for disease progression and treatment effects.
- **Parameter Configurations**: YAML-based configuration files for flexible protocol definitions.
- **Data Analysis**: Tools for analyzing injection intervals, visual acuity changes, and treatment persistence.
- **Visualization**: Generate heatmaps, waterfall plots, and other visualizations for treatment patterns.

## Documentation

Comprehensive documentation for the project is available. To view it, click the link below:

[View Documentation](https://github.com/lh/vegf-1/blob/main/docs/_build/html/index.html)


The documentation includes:
- Setup instructions
- Detailed descriptions of simulation models
- Examples of configuration files
- Analysis and visualization guides

## Repository Structure

```
aided/
├── protocols/                # Configuration files for simulations
│   ├── parameter_sets/       # Parameter sets for different protocols
│   └── simulation_configs/   # Simulation configuration files
├── simulation/               # Core simulation models and logic
├── validation/               # Configuration validation tools
├── visualization/            # Visualization scripts for analysis
├── tests/                    # Unit tests for the project
└── docs/                     # Sphinx documentation source
```

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/lh/vegf-1.git
   cd vegf-1
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run a sample simulation:
   ```bash
   python run_eylea_analysis.py --config protocols/simulation_configs/tests/data/test_vision_config.yaml --output output/
   ```

4. View the results in the `output/` directory.


## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
