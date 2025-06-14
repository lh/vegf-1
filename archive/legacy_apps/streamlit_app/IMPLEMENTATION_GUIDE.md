# Implementation Guide for Refactoring

This guide provides instructions for completing the refactoring of the APE Streamlit application. We have already implemented several key components:

- ✅ Fixed syntax error in app.py
- ✅ Created refactoring plan
- ✅ Implemented core architecture components 
- ✅ Created visualization caching and export functionality
- ✅ Implemented report data models
- ✅ Created Reports and About pages
- ✅ Created a refactored app.py router

## Remaining Implementation Tasks

### 1. Implement Remaining Pages

#### 1.1 Staggered Simulation Page
Extract the staggered simulation code from app.py (lines 709-989) into a dedicated module:

```python
# streamlit_app/pages/staggered_simulation_page.py

def display_staggered_simulation():
    """Display the staggered simulation page."""
    from streamlit_app.components.layout import display_logo_and_title
    display_logo_and_title("Staggered Patient Enrollment Simulation")
    
    # ... (extracted code from app.py lines 709-989)
```

#### 1.2 Patient Explorer Page
Extract the patient explorer code from app.py (lines 990-1073) into a dedicated module:

```python
# streamlit_app/pages/patient_explorer_page.py

def display_patient_explorer_page():
    """Display the patient explorer page."""
    from streamlit_app.components.layout import display_logo_and_title
    display_logo_and_title("Patient Explorer")
    
    # ... (extracted code from app.py lines 990-1073)
```

### 2. Create Remaining Utility Modules

#### 2.1 Config Management
Create a config management module:

```python
# streamlit_app/utils/config.py

def load_config():
    """Load application configuration."""
    # ...
```

#### 2.2 Complete Visualization Components
Create the matplotlib visualization module:

```python
# streamlit_app/components/visualizations/matplotlib_viz.py

def create_va_over_time_plot_matplotlib(data):
    """Create a visual acuity over time plot using matplotlib."""
    # ...

def create_discontinuation_plot_matplotlib(data):
    """Create a discontinuation plot using matplotlib."""
    # ...
```

### 3. Data Models

#### 3.1 Parameter Validation
Create the parameter validation module:

```python
# streamlit_app/models/parameters.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SimulationParameters:
    """Parameters for a simulation."""
    simulation_type: str
    duration_years: float
    population_size: int
    # ...
```

### 4. Testing

#### 4.1 Test Plan
Create a test plan for the refactored application:

```
# streamlit_app/TEST_PLAN.md

## Testing Strategy
1. Unit Tests for Core Components
2. Integration Tests for Page Flows
3. Manual Testing Checklist
```

## Refactoring Workflow

1. **Extract Pages Incrementally**: Extract each page one at a time, testing after each extraction
2. **Use Feature Flags**: Implement a feature flag system to toggle between old and new versions
3. **Preserve State**: Ensure state is maintained between the old and new implementations
4. **Refactor Imports**: Update imports to use the new structure
5. **Add Logging**: Add comprehensive logging to help debug any issues

## Running the Refactored Application

During development, you can test the refactored version alongside the original:

```bash
# Run original version
streamlit run app.py

# Run refactored version
streamlit run app_refactored.py
```

## Code Quality Checks

Before finalizing the refactoring:

1. **Code Formatting**: Ensure consistent formatting using a tool like Black
2. **Linting**: Run pylint or flake8 to check for code quality issues
3. **Type Checking**: Add type hints and run mypy for type checking
4. **Documentation**: Ensure all modules, classes, and functions have proper docstrings

## Deployment Considerations

When ready to deploy the refactored version:

1. **Backup**: Create a backup of the original code
2. **Rename Files**: Rename app_refactored.py to app.py
3. **Test Thoroughly**: Test the deployed version extensively
4. **Rollback Plan**: Have a plan for rolling back if issues are encountered

## Directory Structure Reminder

```
streamlit_app/
├── app.py                   # Main entry point
├── pages/                   # Page components
│   ├── dashboard.py         # Dashboard page
│   ├── run_simulation.py    # Run Simulation page
│   ├── staggered_simulation_page.py
│   ├── patient_explorer_page.py
│   ├── reports_page.py     
│   └── about_page.py       
├── components/              # UI components
│   ├── layout.py           
│   ├── visualizations/     
│   │   ├── __init__.py     
│   │   ├── matplotlib_viz.py
│   │   ├── r_integration.py
│   │   ├── common.py       
│   │   ├── cache.py        
│   │   └── export.py       
│   ├── metrics_display.py  
│   └── data_tables.py      
├── utils/                   # Utilities
│   ├── session_state.py    
│   ├── simulation_utils.py 
│   ├── config.py           
│   └── error_handling.py   
└── models/                  # Data models
    ├── __init__.py
    ├── simulation_results.py
    ├── parameters.py       
    └── report.py          
```

## Achievement Tracking

As components are completed, update the implementation status in the README or documentation to track progress.