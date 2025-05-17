# APE: AMD Protocol Explorer

An interactive Streamlit dashboard for exploring and visualizing AMD treatment protocols using Discrete Event Simulation (DES) and Agent-Based Simulation (ABS).

## Overview

APE (AMD Protocol Explorer) provides an interactive interface for exploring AMD treatment protocols through simulation. The tool incorporates both DES and ABS approaches with detailed modeling of discontinuation patterns, clinician variation, and time-dependent recurrence probabilities based on clinical data.

## Features

- **Interactive Visualization**: Explore simulation results through interactive charts and tables
- **Customizable Simulations**: Configure simulation parameters to test different scenarios
- **Detailed Reports**: Generate comprehensive reports with Quarto integration
- **Model Validation**: Compare simulation results with clinical data
- **Patient Explorer**: Examine individual patient treatment journeys
- **Debug Mode**: Toggle detailed diagnostic information for troubleshooting
- **Fixed Discontinuation Tracking**: Accurate discontinuation rates with unique patient tracking
- **Staggered Patient Enrollment**: Realistic patient enrollment patterns using Poisson distribution
- **Dual Timeframe Analysis**: Calendar time vs. patient time (weeks since enrollment) analysis
- **Puppeteer Integration**: Support for automated testing and AI assistant navigation

## Setup and Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git (to clone the repository)

### Quick Start

The easiest way to launch the dashboard is to use the setup script and run script:

```bash
# Install dependencies and set up directories
python setup_streamlit.py

# Launch the application with fixed discontinuation implementation
python run_ape.py
```

The dashboard will be available at http://localhost:8502 by default.

### Manual Setup

If you prefer to set up manually:

1. Install the required dependencies:

```bash
pip install -r streamlit_requirements.txt
```

2. Run the Streamlit app directly:

```bash
streamlit run streamlit_app/app.py
```

### Puppeteer Integration

For automated testing and AI assistant navigation, we provide Puppeteer integration:

1. Install Node.js dependencies:

```bash
cd streamlit_app
npm install
```

2. Run test scripts:

```bash
# Basic integration test
npm run test

# Visual regression testing (baseline mode)
npm run visual:baseline

# Visual regression testing (comparison mode)
npm run visual:test
```

See `PUPPETEER_AUTOMATION.md` for complete documentation on the Puppeteer integration.

### Environment Variables

You can customize app behavior using environment variables:

- `APE_DEFAULT_SIMULATION`: Set the default simulation configuration name
- `APE_ENABLE_DEBUG`: Set to "true" to enable debug information by default
- `IS_STREAMLIT_CLOUD`: Set to "true" to force Streamlit Cloud environment detection

Set these variables in your shell or add a `.streamlit/secrets.toml` file.

## Using the Dashboard

### Navigation

The application has five main sections accessible from the sidebar:

1. **Dashboard**: Overview of simulation results with visualizations
2. **Run Simulation**: Configure and run new simulations
3. **Staggered Simulation**: Run simulations with realistic patient enrollment patterns
4. **Patient Explorer**: Analyze individual patient treatment journeys
5. **Reports**: Generate detailed Quarto reports
6. **About**: Information about the application

### Running Simulations

1. Navigate to the "Run Simulation" tab
2. Select simulation type (ABS or DES)
3. Set duration (years) and population size
4. Configure discontinuation parameters:
   - Enable/disable clinician variation
   - Set planned discontinuation probability
   - Adjust administrative discontinuation probability
   - Configure premature discontinuation factors
5. Expand "Advanced Options" for more settings
6. Click "Run Simulation" to execute

### Staggered Patient Enrollment

For more realistic simulation of clinical trials:

1. Navigate to the "Staggered Simulation" tab
2. Set duration (years) and target population size
3. Adjust patient arrival rate (patients per week)
4. Click "Run Staggered Simulation" to execute
5. Explore dual timeframe visualizations showing:
   - Calendar time analysis (real-world timeline)
   - Patient time analysis (weeks since enrollment)
   - Enrollment distribution over time
   - Sample size awareness in confidence intervals

### Debug Mode

The application includes a debug mode for troubleshooting:

1. Toggle "🛠️ Debug Mode" in the sidebar
2. When enabled, detailed diagnostic information will be displayed
3. This includes additional debug messages, raw simulation stats, and data structure details

Debug mode is helpful for:
- Diagnosing simulation issues
- Understanding the data structures
- Verifying discontinuation tracking
- Comparing raw event counts vs. unique patient counts

## Discontinuation Model

This application implements an enhanced discontinuation model that correctly tracks unique patient discontinuations:

- Properly tracks each patient's discontinuation status
- Prevents double-counting of discontinuations
- Reports accurate discontinuation rates (≤100%)
- Distinguishes between discontinuation events and unique patient count
- Tracks retreatments by discontinuation type

## Directory Structure

```
streamlit_app/
├── app.py                      # Main Streamlit application
├── acknowledgments.py          # Acknowledgments information
├── amd_protocol_explorer.py    # Dashboard implementation
├── patient_explorer.py         # Patient-level exploration
├── retreatment_panel.py        # Retreatment analysis panel
├── simulation_runner.py        # Simulation execution and processing
├── json_utils.py               # JSON serialization utilities
├── monkey_patch.py             # Runtime patches for compatibility
├── quarto_utils.py             # Utilities for Quarto integration
├── puppeteer_helpers.py        # Helpers for Puppeteer integration
├── test_puppeteer_integration.js # Puppeteer test script
├── visual_regression.js        # Visual regression testing
├── PUPPETEER_AUTOMATION.md     # Puppeteer documentation
├── puppeteer_integration_guide.md # Integration guide
├── add_puppeteer_markers.py    # Helper for adding markers
├── assets/                     # Static assets (logos, images)
│   └── ape_logo.svg            # APE logo
├── reports/                    # Quarto report templates
│   └── simulation_report.qmd   # Template for simulation reports
├── screenshots/                # Test screenshots directory
└── requirements.txt            # Python dependencies
```

## Streamlit Cloud Deployment

For cloud deployment, see the `deployment_guide.md` file for detailed instructions.

## AI Assistant Integration

The app includes special markers and helper functions to make it accessible to AI assistants like Claude. This enables:

- Automated navigation between app sections
- Running simulations with specific parameters
- Testing visualization and report generation
- Patient data exploration

For Claude or similar AI assistants, use the `test_puppeteer_integration.js` script as a reference for interacting with the app.

## Troubleshooting

- If you encounter import errors, verify your Python path includes the project root
- For visualization issues, check the simulation results structure
- Use debug mode to see detailed diagnostic information
- If discontinuation rates exceed 100%, ensure you're using the fixed implementation
- For Puppeteer integration issues, see the troubleshooting section in `PUPPETEER_AUTOMATION.md`

## Acknowledgments

This Streamlit dashboard was developed with inspiration from the [Project_Toy_MECC](https://github.com/DomRowney/Project_Toy_MECC) 
repository originally created by Dom Rowney, with further development at 
[Bergam0t/Project_Toy_MECC](https://github.com/Bergam0t/Project_Toy_MECC).

Special thanks to Sammi Rosser for their work on the Quarto integration for report generation,
including the innovative approach to installing Quarto within Streamlit Cloud environments.