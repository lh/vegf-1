# APE: AMD Protocol Explorer

An interactive dashboard for exploring AMD treatment protocols using Discrete Event Simulation (DES) and Agent-Based Simulation (ABS).

## Overview

APE (AMD Protocol Explorer) provides an interactive interface for exploring AMD treatment protocols through simulation. The tool incorporates both DES and ABS approaches with detailed modeling of discontinuation patterns, clinician variation, and time-dependent recurrence probabilities based on clinical data.

## Running the Application

There are two ways to run the application:

### Option 1: Run directly from the project root (Recommended)

```bash
python run_ape.py
```

This method ensures the correct Python path is set for importing simulation modules.

### Option 2: Run using Streamlit directly

```bash
cd /path/to/project/root
streamlit run streamlit_app/app.py
```

When using this method, make sure you're running the command from the project root directory to ensure proper imports.

## Features

- **Interactive Visualization**: Explore simulation results through interactive charts and tables
- **Customizable Simulations**: Configure simulation parameters to test different scenarios
- **Detailed Reports**: Generate comprehensive reports with Quarto integration
- **Model Validation**: Compare simulation results with clinical data

## Troubleshooting

If you encounter issues running the simulation:

1. **Import Errors**: Make sure you're running the application from the project root directory
2. **Environment Issues**: Ensure all required dependencies are installed (see requirements.txt)
3. **Module Not Found**: The app will fallback to sample data if simulation modules can't be found

## Acknowledgments

This Streamlit dashboard was developed with inspiration from the Project_Toy_MECC repository originally created by Dom Rowney, with further development at Bergam0t/Project_Toy_MECC. Special thanks to Sammi Rosser for their work on the Quarto integration for report generation.