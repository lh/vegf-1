# Streamgraph Visualization Environment Setup

This guide explains how to set up your environment to run the streamgraph visualization code.

## Environment Requirements

This project was developed using Python 3.12 with the following main dependencies:
- numpy
- pandas
- matplotlib
- streamlit (for web app visualization)
- Mesa (for agent-based simulation)

## Setup Options

### Option 1: Using Virtual Environment (Recommended for quick testing)

For a simple Python virtual environment:

```bash
# Make the script executable if needed
chmod +x setup_venv.sh

# Run the setup script
./setup_venv.sh

# To also install development dependencies (optional)
./setup_venv.sh --with-dev
```

This will:
1. Create a Python virtual environment in a `venv` directory
2. Install a minimal set of required dependencies from requirements_minimal.txt
3. Activate the environment for you

### Option 2: Using Conda Environment

If you prefer using conda:

```bash
# Make the script executable if needed
chmod +x setup_conda.sh

# Run the setup script
./setup_conda.sh
```

This will:
1. Create a conda environment named 'macular-simulation'
2. Install core dependencies from environment.yaml
3. Install additional dependencies from requirements_minimal.txt
4. Activate the environment for you

## Running the Streamgraph Test

Once your environment is set up, you can run the streamgraph test with:

```bash
python run_streamgraph_phase_test.py --patients 50 --years 3 --plot
```

This will:
1. Run a simulation with 50 patients over 3 years
2. Generate a streamgraph visualization showing patient states
3. Save the results and visualization to file

## Command-line Options

The test script supports the following options:

- `--patients` or `-p`: Number of patients to simulate (default: 100)
- `--years` or `-y`: Duration of simulation in years (default: 5)
- `--output` or `-o`: Custom output file path
- `--plot` or `-g`: Generate the streamgraph visualization

Example with all options:
```bash
python run_streamgraph_phase_test.py -p 200 -y 5 -o output/my_simulation.json -g
```

## Troubleshooting

If you encounter any issues:

1. Make sure your Python version is 3.10 or higher
2. Check that all dependencies are correctly installed
3. Verify that the simulation configuration files are present in the protocols directory