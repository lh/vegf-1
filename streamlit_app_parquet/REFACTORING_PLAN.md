# Streamlit App Refactoring Plan

## Overview

The current `app.py` file (1,233 lines) has grown too large and monolithic, making it difficult to maintain and extend. This document outlines a comprehensive refactoring plan to break down the application into smaller, more manageable modules with clear responsibilities.

## Directory Structure

```
streamlit_app/
├── app.py                   # Main entry point (thin router)
├── pages/                   # Page components
│   ├── dashboard.py         # Dashboard page
│   ├── run_simulation.py    # Run Simulation page
│   ├── staggered_simulation_page.py # Staggered Simulation page
│   ├── patient_explorer_page.py # Patient Explorer page
│   ├── reports_page.py      # Reports page
│   └── about_page.py        # About page
├── components/              # Reusable UI components
│   ├── layout.py            # Layout components (logo, sidebar, footer)
│   ├── visualizations/      # Visualization components
│   │   ├── __init__.py      # Exports all visualization functions
│   │   ├── matplotlib_viz.py # Matplotlib-based visualizations
│   │   ├── r_integration.py # R-based visualization integration
│   │   ├── common.py        # Shared visualization utilities
│   │   ├── cache.py         # Visualization caching system
│   │   └── export.py        # Export visualizations to various formats
│   ├── metrics_display.py   # Reusable metrics visualization components
│   └── data_tables.py       # Reusable data table components
├── utils/                   # Utility functions
│   ├── session_state.py     # Session state management
│   ├── simulation_utils.py  # Simulation helper functions
│   ├── config.py            # Configuration management
│   └── error_handling.py    # Error handling utilities
├── models/                  # Data models and type definitions
│   ├── __init__.py
│   ├── simulation_results.py # Simulation results data model
│   ├── parameters.py        # Parameter definitions and validation
│   └── report.py            # Report data structures
└── ... (existing files)
```

## Refactoring Steps

### 1. Create Layout Components (`layout.py`)

Extract layout-related functions from `app.py`:
- `display_logo_and_title()` function
- Sidebar navigation code
- Footer rendering

These components will be used across multiple pages.

### 2. Extract Page Modules

Create separate modules for each page in the application:

#### 2.1. Dashboard Page (`dashboard.py`)
- Extract code from lines 231-320
- Function: `display_dashboard()`

#### 2.2. Run Simulation Page (`run_simulation.py`)
- Extract code from lines 322-707
- Function: `display_run_simulation()`

#### 2.3. Staggered Simulation Page (`staggered_simulation_page.py`)
- Extract code from lines 709-989
- Function: `display_staggered_simulation()`

#### 2.4. Patient Explorer Page (`patient_explorer_page.py`)
- Extract code from lines 990-1073
- Function: `display_patient_explorer_page()`
- Note: This already uses `display_patient_explorer()` from a separate module

#### 2.5. Reports Page (`reports_page.py`)
- Extract code from lines 1074-1190
- Function: `display_reports_page()`

#### 2.6. About Page (`about_page.py`)
- Extract code from lines 1192-1229
- Function: `display_about_page()`

### 3. Create Utility and Model Modules

#### 3.1. Session State Management (`utils/session_state.py`)
- Functions to get/set session state variables
- Initialize default state values
- Helper methods for preserving state between page navigations

#### 3.2. Error Handling (`utils/error_handling.py`)
- Standardized error handling and display components
- Error logging utilities
- User-friendly error messages with detailed debugging information

#### 3.3. Configuration Management (`utils/config.py`)
- Loading and managing application configuration
- Environment-specific settings
- Feature flags management

#### 3.4. Data Models (`models/` directory)
- Type definitions using Python dataclasses or Pydantic models
- Input parameter validation
- Standardized result objects
- Consistent data structures across modules

### 4. Refactor Main App (`app.py`)

Simplify the main app to become a thin router:
- Import necessary dependencies
- Set up page configuration
- Handle navigation via sidebar
- Route to the appropriate page module based on selected page
- Manage shared state

### 5. Dependency Management

For each module:
- Import only the dependencies needed for that module
- Localize imports to reduce interdependencies
- Handle import errors gracefully at the module level

## Benefits

1. **Improved Maintainability**: Smaller, focused files with clear responsibilities
2. **Better Collaboration**: Team members can work on different components without conflicts
3. **Easier Testing**: Components can be tested in isolation
4. **Enhanced Readability**: Logical organization makes code easier to understand
5. **Scalability**: New pages and features can be added more easily

## Implementation Approach

1. Create new directory structure
2. Implement base layout components first
3. Extract one page at a time, starting with simpler pages
4. Test each extracted component individually
5. Gradually transform the main app.py into the router
6. Conduct comprehensive testing to ensure no functionality is lost

## Implementation Phases

### Phase 1: Core Architecture
1. Create directory structure
2. Extract shared components (layout, session state)
3. Create visualization framework with both matplotlib and R-based options
4. Create error handling utilities
5. Implement a simple page (e.g., About) to validate the architecture

### Phase 2: Feature Migration
1. Extract each page module one at a time
2. Implement shared data models for parameters and results
3. Create metrics display components to standardize visualizations
4. Ensure backward compatibility with existing session state

### Phase 3: Router Implementation and Testing
1. Create the thin router app.py
2. Add automated tests for each component
3. Add integration tests for the complete application
4. Comprehensive test plan for all features

### Phase 4: Enhancements
1. Add type hints throughout the codebase
2. Add comprehensive documentation
3. Optimize performance for large datasets
4. Implement progressive loading for slow operations

## Notes and Best Practices

- Use relative imports within the package
- Maintain consistent naming conventions
- Add docstrings to all new modules and functions
- Implement proper error boundaries for each component
- Add logging throughout the application for better debugging
- Follow a consistent input/output pattern for all component functions
- Create unit tests for core functionality
- Consider adding type hints with mypy validation
- Use feature flags for new functionality to enable gradual rollout
- Consider implementing lazy loading for heavy components
- Use context managers for resource management (e.g., R script execution)
- Ensure backward compatibility with existing functionality
- Add timing metrics to identify performance bottlenecks