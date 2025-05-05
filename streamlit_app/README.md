# Enhanced Discontinuation Model Dashboard

An interactive Streamlit dashboard for visualizing and analyzing the Enhanced Discontinuation Model for AMD treatment simulations.

## Overview

This dashboard provides an interactive interface for exploring simulation results from the Enhanced Discontinuation Model. The model incorporates multiple discontinuation types, clinician variation, and time-dependent recurrence probabilities based on clinical data.

## Features

- **Interactive Visualization**: Explore simulation results through interactive charts and tables
- **Customizable Simulations**: Configure simulation parameters to test different scenarios
- **Detailed Reports**: Generate comprehensive reports with Quarto integration
- **Model Validation**: Compare simulation results with clinical data

## Setup and Installation

### Local Development

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:

```bash
streamlit run app.py
```

### Streamlit Cloud Deployment

The app is designed to be deployed on Streamlit Cloud with automatic Quarto installation. To deploy:

1. Push your code to a GitHub repository
2. Connect the repository to Streamlit Cloud
3. Set the main file path to `streamlit_app/app.py`
4. The app will automatically install Quarto at runtime for report generation

## Directory Structure

```
streamlit_app/
├── app.py                      # Main Streamlit application
├── acknowledgments.py          # Acknowledgments information
├── enhanced_discontinuation_dashboard.py  # Dashboard implementation
├── quarto_utils.py             # Utilities for Quarto integration
├── reports/                    # Quarto report templates
│   └── simulation_report.qmd   # Template for simulation reports
└── requirements.txt            # Python dependencies
```

## Acknowledgments

This Streamlit dashboard was developed with inspiration from the [Project_Toy_MECC](https://github.com/DomRowney/Project_Toy_MECC) 
repository originally created by Dom Rowney, with further development at 
[Bergam0t/Project_Toy_MECC](https://github.com/Bergam0t/Project_Toy_MECC).

Special thanks to Sammi Rosser for their work on the Quarto integration for report generation,
including the innovative approach to installing Quarto within Streamlit Cloud environments.

## Usage

1. Navigate to the dashboard page to view simulation results
2. Use the "Run Simulation" page to configure and run new simulations
3. Generate detailed reports using the "Reports" page
4. Learn more about the model on the "About" page