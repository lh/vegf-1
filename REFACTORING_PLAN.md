# VEGF-1 Repository Refactoring Plan

## Overview
This document outlines a comprehensive refactoring plan to modernize the repository structure, consolidate multiple Streamlit apps, and follow Python best practices. The refactoring will be executed on a new branch without affecting the current main branch.

## Current State Analysis

### Repository Structure Issues
1. **Multiple Streamlit app directories**: `streamlit_app`, `streamlit_app_v2`, `streamlit_app_parquet`
2. **Scattered simulation code**: `simulation/`, `simulation_v2/`
3. **APE.py buried in subdirectory**: Currently at `streamlit_app_v2/APE.py`
4. **Duplicated utilities**: Each streamlit app has its own utils directory
5. **Non-standard project layout**: Makes deployment and imports complex

### Key Assets to Preserve
- APE.py (main Streamlit application)
- simulation_v2 (latest simulation engine)
- protocols (treatment protocol definitions)
- visualization utilities
- Test suites
- Documentation
- Submodules for copyright-sensitive data

## Target Structure

```
vegf-1/
├── APE.py                          # Main Streamlit app (moved from streamlit_app_v2/)
├── requirements.txt                # Single consolidated requirements file
├── README.md                       # Main project documentation
├── .gitignore                      # Already updated with LaTeX artifacts
├── CLAUDE.md                       # Development instructions
│
├── ape/                           # Core application modules
│   ├── __init__.py
│   ├── pages/                     # Streamlit pages
│   │   ├── __init__.py
│   │   ├── simulation.py          # Run Simulation page
│   │   ├── analysis.py            # Calendar-Time Analysis page
│   │   ├── patient_explorer.py   # Patient Explorer page
│   │   └── economics.py          # Economic Analysis page
│   ├── components/                # Reusable UI components
│   │   ├── __init__.py
│   │   ├── sidebar.py
│   │   ├── visualizations.py
│   │   └── data_display.py
│   └── utils/                     # Application utilities
│       ├── __init__.py
│       ├── session_state.py
│       └── file_management.py
│
├── simulation/                     # Consolidated simulation engine
│   ├── __init__.py
│   ├── core/                      # From simulation_v2/core
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── patient.py
│   │   └── state_machine.py
│   ├── economics/                 # Economic modeling
│   │   ├── __init__.py
│   │   ├── cost_model.py
│   │   └── carbon_model.py
│   ├── protocols/                 # Treatment protocols
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── definitions/
│   └── analysis/                  # Analysis tools
│       ├── __init__.py
│       ├── calendar_time.py
│       └── patient_level.py
│
├── visualization/                  # Visualization modules
│   ├── __init__.py
│   ├── color_system.py            # Central color system
│   ├── charts/
│   │   ├── __init__.py
│   │   ├── acuity.py
│   │   ├── streamgraph.py
│   │   └── economics.py
│   └── templates/                 # Tufte-style templates
│
├── data/                          # Data files
│   ├── protocols/                 # Protocol JSON files
│   ├── parameters/                # Parameter sets
│   └── sample/                    # Sample data for testing
│
├── output/                        # Generated outputs
│   ├── simulations/              # Simulation results
│   ├── visualizations/           # Generated charts
│   └── reports/                  # Analysis reports
│
├── tests/                         # All tests consolidated
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── user_guide/               # User documentation
│   └── development/              # Developer documentation
│
├── scripts/                       # Utility scripts
│   ├── migrate_data.py           # Data migration scripts
│   ├── validate_protocols.py     # Protocol validation
│   └── deploy.py                 # Deployment helpers
│
├── notebooks/                     # Jupyter notebooks
│   └── examples/                 # Example analyses
│
├── Paper/                        # Academic paper (unchanged)
│   └── medical-computing-paper/
│
└── submodules/                   # Git submodules (unchanged)
    ├── aflibercept_2mg_data/
    ├── eylea_high_dose_data/
    └── vegf_literature_data/
```

## Refactoring Steps

### Phase 1: Create New Branch and Directory Structure
```bash
git checkout -b feature/repository-refactor
mkdir -p ape/{pages,components,utils}
mkdir -p simulation/{core,economics,protocols,analysis}
mkdir -p visualization/{charts,templates}
mkdir -p data/{protocols,parameters,sample}
mkdir -p output/{simulations,visualizations,reports}
mkdir -p tests/{unit,integration}
mkdir -p docs/{api,user_guide,development}
mkdir -p scripts
mkdir -p notebooks/examples
```

### Phase 2: Move Core Files
1. **Move APE.py to root**:
   ```bash
   cp streamlit_app_v2/APE.py ./
   ```

2. **Consolidate simulation code**:
   - Move `simulation_v2/core/*` → `simulation/core/`
   - Move `simulation_v2/economics/*` → `simulation/economics/`
   - Move protocol definitions → `simulation/protocols/`

3. **Consolidate visualization code**:
   - Move color system → `visualization/color_system.py`
   - Move chart components → `visualization/charts/`

### Phase 3: Update Imports

#### Example Import Changes:
```python
# Old import in APE.py:
from pages.simulation import simulation_page
from utils.session_state import init_session_state

# New import:
from ape.pages.simulation import simulation_page
from ape.utils.session_state import init_session_state

# Old import for simulation:
from simulation_v2.core.engine import SimulationEngine

# New import:
from simulation.core.engine import SimulationEngine
```

### Phase 4: Consolidate Duplicate Code

#### Identify and merge:
1. **Utils modules** from all three streamlit apps
2. **Visualization components** - standardize on best implementations
3. **Data loading functions** - create single data module
4. **Test utilities** - consolidate test fixtures

### Phase 5: Update Configuration Files

1. **requirements.txt**: Already consolidated on main
2. **Update paths in**:
   - `.gitignore` (if needed)
   - `CLAUDE.md`
   - GitHub Actions workflows
   - Documentation

### Phase 6: Create Migration Scripts

```python
# scripts/migrate_simulations.py
"""
Script to migrate existing simulation results to new structure
"""

# scripts/update_imports.py
"""
Script to automatically update import statements
"""
```

## Import Path Mapping

| Old Path | New Path |
|----------|----------|
| `streamlit_app_v2/APE.py` | `APE.py` |
| `streamlit_app_v2/pages/*` | `ape/pages/*` |
| `streamlit_app_v2/utils/*` | `ape/utils/*` |
| `simulation_v2/core/*` | `simulation/core/*` |
| `simulation_v2/economics/*` | `simulation/economics/*` |
| `protocols/*` | `simulation/protocols/definitions/*` |
| `visualization/color_system.py` | `visualization/color_system.py` (unchanged) |

## Benefits of Refactoring

1. **Standard Python project structure**: Easier onboarding and tooling
2. **Simplified deployment**: `streamlit run APE.py` from root
3. **Cleaner imports**: Logical module hierarchy
4. **Better code reuse**: Consolidated utilities and components
5. **Easier testing**: Single test suite location
6. **Improved CI/CD**: Standard structure for GitHub Actions
7. **Better documentation**: Clear module organization

## Risk Mitigation

1. **Preserve working code**: Use git mv instead of mv when possible
2. **Maintain backwards compatibility**: Create import shims if needed
3. **Test incrementally**: Run tests after each major move
4. **Document changes**: Update all documentation as we go
5. **Keep submodules intact**: Don't touch copyright-sensitive data

## Execution Timeline

1. **Week 1**: Directory structure and core file movements
2. **Week 2**: Import updates and code consolidation
3. **Week 3**: Testing and documentation updates
4. **Week 4**: Final validation and merge preparation

## Success Criteria

- [ ] APE.py runs from root directory
- [ ] All tests pass with new structure
- [ ] Imports are clean and logical
- [ ] No duplicate code remains
- [ ] Documentation is updated
- [ ] Deployment is simplified
- [ ] CI/CD workflows function correctly

## Notes

- This refactoring maintains all existing functionality
- Legacy app directories can be archived after validation
- Consider creating an `archive/` directory for old implementations
- The refactoring can be done incrementally with working commits

## Next Steps

1. Review and approve this plan
2. Create feature branch
3. Begin Phase 1 implementation
4. Regular testing and validation
5. Stakeholder review before merge