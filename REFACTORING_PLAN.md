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
6. **Multiple visualization implementations**: 17+ different streamgraph_*.py files in streamlit_app_parquet
7. **Scattered test files**: Test files mixed with application code
8. **R integration files**: R scripts scattered across multiple directories

### Key Assets to Preserve
- APE.py (main Streamlit application from streamlit_app_v2)
- simulation_v2 (latest simulation engine with DES capabilities)
- protocols (treatment protocol definitions)
- visualization utilities (especially the central color system)
- Test suites (including Playwright integration tests)
- Documentation (including meta/ insights)
- Submodules for copyright-sensitive data (keep at root level)
- R integration capabilities
- Carbon accounting features
- Validation tools

## Target Structure

```
vegf-1/
├── APE.py                          # Main Streamlit app (moved from streamlit_app_v2/)
├── requirements.txt                # Single consolidated requirements file
├── requirements-dev.txt            # Development dependencies
├── README.md                       # Main project documentation
├── .gitignore                      # Already updated with LaTeX artifacts
├── CLAUDE.md                       # Development instructions
├── pyproject.toml                  # Modern Python project config
│
├── ape/                           # Core application modules
│   ├── __init__.py
│   ├── pages/                     # Streamlit pages
│   │   ├── __init__.py
│   │   ├── simulation.py          # Run Simulation page
│   │   ├── analysis.py            # Calendar-Time Analysis page
│   │   ├── patient_explorer.py   # Patient Explorer page
│   │   ├── economics.py          # Economic Analysis page
│   │   └── saved_simulations.py  # Manage saved results
│   ├── components/                # Reusable UI components
│   │   ├── __init__.py
│   │   ├── sidebar.py
│   │   ├── data_display.py
│   │   └── file_browser.py       # Simulation file browser
│   ├── utils/                     # Application utilities
│   │   ├── __init__.py
│   │   ├── session_state.py
│   │   ├── file_management.py
│   │   └── data_loader.py        # Consolidated data loading
│   └── r_integration/             # R integration modules
│       ├── __init__.py
│       ├── r_bridge.py
│       └── scripts/               # R scripts
│
├── simulation/                     # Consolidated simulation engine
│   ├── __init__.py
│   ├── core/                      # From simulation_v2/core
│   │   ├── __init__.py
│   │   ├── engine.py              # Main DES engine
│   │   ├── patient.py            # Patient model
│   │   ├── state_machine.py      # State transitions
│   │   └── events.py             # Event handling
│   ├── economics/                 # Economic modeling
│   │   ├── __init__.py
│   │   ├── cost_model.py         # Cost calculations
│   │   ├── carbon_model.py       # Carbon accounting
│   │   └── pricing.py            # Drug pricing data
│   ├── protocols/                 # Treatment protocols
│   │   ├── __init__.py
│   │   ├── base.py               # Protocol interfaces
│   │   ├── definitions/          # Protocol JSON files
│   │   └── validation.py         # Protocol validation
│   └── analysis/                  # Analysis tools
│       ├── __init__.py
│       ├── calendar_time.py      # Calendar-time transformation
│       ├── patient_level.py      # Patient-level analysis
│       └── discontinuation.py    # Discontinuation tracking
│
├── visualization/                  # Visualization modules
│   ├── __init__.py
│   ├── color_system.py            # Central color system (SINGLE SOURCE)
│   ├── charts/
│   │   ├── __init__.py
│   │   ├── acuity.py             # Visual acuity charts
│   │   ├── streamgraph.py        # CONSOLIDATED streamgraph
│   │   ├── economics.py          # Economic visualizations
│   │   ├── enrollment.py         # Enrollment timeline
│   │   └── base.py               # Base chart classes
│   └── templates/                 # Tufte-style templates
│       ├── __init__.py
│       └── styles.py              # Consistent styling
│
├── data/                          # Static data files
│   ├── protocols/                 # Protocol JSON definitions
│   ├── parameters/                # Parameter sets
│   └── reference/                 # Reference data (NOT synthetic)
│
├── output/                        # Generated outputs (gitignored)
│   ├── simulations/              # Simulation results
│   ├── visualizations/           # Generated charts
│   ├── reports/                  # Analysis reports
│   └── debug/                    # Debug outputs
│
├── tests/                         # All tests consolidated
│   ├── __init__.py
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── playwright/               # Browser automation tests
│   │   ├── test_app.py
│   │   └── debug_scripts/        # Playwright debug tools
│   ├── fixtures/                 # Test fixtures
│   └── validation/               # Scientific validation tests
│
├── meta/                          # Project insights (preserved)
│   ├── visualization_templates.md
│   ├── streamgraph_synthetic_data_postmortem.md
│   └── debug/                    # Debug documentation
│
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── user_guide/               # User documentation
│   ├── development/              # Developer documentation
│   └── scientific/               # Scientific methodology
│
├── scripts/                       # Utility scripts
│   ├── migrate_simulations.py    # Migrate existing results
│   ├── update_imports.py         # Automated import updates
│   ├── validate_protocols.py     # Protocol validation
│   ├── consolidate_streamgraphs.py # Merge streamgraph variants
│   └── pre_commit_checks.py      # Pre-commit validation
│
├── tools/                         # Development tools
│   ├── playwright/                # Playwright configs
│   └── linting/                  # Linting configs
│
├── validation/                    # Scientific validation (preserved)
│   └── verify_*.py               # Validation scripts
│
├── notebooks/                     # Jupyter notebooks
│   └── examples/                 # Example analyses
│
├── archive/                       # Legacy code (temporary)
│   ├── streamlit_app/            # Old app version
│   ├── streamlit_app_parquet/    # Parquet version
│   └── simulation_v1/            # Old simulation engine
│
├── Paper/                        # Academic paper (unchanged)
│   └── medical-computing-paper/
│
├── designer/                      # Design tools (preserved)
├── mcp/                          # MCP servers (preserved)
│
# Submodules remain at root level (unchanged location)
├── aflibercept_2mg_data/         # Git submodule
├── eylea_high_dose_data/         # Git submodule
└── vegf_literature_data/         # Git submodule
```

## Refactoring Steps

### Phase 0: Pre-refactoring Analysis and Preparation
1. **Dependency Analysis**:
   ```bash
   # Generate import dependency graph
   python scripts/analyze_imports.py > import_dependencies.txt
   
   # Identify circular dependencies
   python scripts/find_circular_imports.py
   ```

2. **Create Migration Tools**:
   ```python
   # scripts/update_imports.py - Automated import updater
   # scripts/validate_migration.py - Verify file moves
   # scripts/test_runner.py - Run tests after each phase
   ```

3. **Backup Current State**:
   ```bash
   git tag pre-refactor-backup
   ```

### Phase 1: Create New Branch and Directory Structure
```bash
git checkout -b feature/repository-refactor

# Create new structure
mkdir -p ape/{pages,components,utils,r_integration/scripts}
mkdir -p simulation/{core,economics,protocols/definitions,analysis}
mkdir -p visualization/{charts,templates}
mkdir -p data/{protocols,parameters,reference}
mkdir -p output/{simulations,visualizations,reports,debug}
mkdir -p tests/{unit,integration,playwright/debug_scripts,fixtures,validation}
mkdir -p docs/{api,user_guide,development,scientific}
mkdir -p scripts tools/{playwright,linting}
mkdir -p notebooks/examples
mkdir -p archive/{streamlit_app,streamlit_app_parquet,simulation_v1}

# Create __init__.py files
find ape simulation visualization tests -type d -exec touch {}/__init__.py \;
```

### Phase 2: Move Core Files (Using git mv for history preservation)
1. **Move APE.py to root**:
   ```bash
   git mv streamlit_app_v2/APE.py ./
   ```

2. **Consolidate simulation code**:
   ```bash
   # Core simulation engine
   git mv simulation_v2/core/* simulation/core/
   git mv simulation_v2/economics/* simulation/economics/
   git mv simulation_v2/protocols/* simulation/protocols/
   
   # Analysis tools
   git mv streamlit_app_parquet/calendar_time_analysis.py simulation/analysis/calendar_time.py
   git mv streamlit_app_parquet/patient_explorer.py simulation/analysis/patient_level.py
   ```

3. **Consolidate visualization code**:
   ```bash
   # Move central color system (already in correct place)
   # Consolidate streamgraph implementations
   python scripts/consolidate_streamgraphs.py
   
   # Move chart components
   git mv streamlit_app_v2/visualizations/acuity_charts.py visualization/charts/acuity.py
   ```

4. **Move Streamlit pages**:
   ```bash
   git mv streamlit_app_v2/pages/* ape/pages/
   ```

5. **Consolidate utilities**:
   ```bash
   # Merge utils from all three apps
   python scripts/merge_utils.py
   ```

6. **Move R integration**:
   ```bash
   git mv streamlit_app*/r_scripts/* ape/r_integration/scripts/
   git mv streamlit_app_parquet/r_integration.py ape/r_integration/r_bridge.py
   ```

7. **Move tests**:
   ```bash
   git mv tests/unit/* tests/unit/
   git mv tests/integration/* tests/integration/
   git mv streamlit_app*/test_*.py tests/integration/
   git mv streamlit_app*/playwright_*.js tests/playwright/debug_scripts/
   ```

8. **Archive old directories**:
   ```bash
   git mv streamlit_app archive/
   git mv streamlit_app_parquet archive/
   git mv simulation archive/simulation_v1
   ```

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
| `streamlit_app_v2/components/*` | `ape/components/*` |
| `simulation_v2/core/*` | `simulation/core/*` |
| `simulation_v2/economics/*` | `simulation/economics/*` |
| `simulation_v2/protocols/*` | `simulation/protocols/*` |
| `protocols/*` | `simulation/protocols/definitions/*` |
| `visualization/color_system.py` | `visualization/color_system.py` (unchanged) |
| `streamlit_app_parquet/streamgraph_*.py` | `visualization/charts/streamgraph.py` |
| `streamlit_app*/r_scripts/*` | `ape/r_integration/scripts/*` |
| `validation/*.py` | `validation/*.py` (unchanged) |

## Automated Import Update Strategy

```python
# scripts/update_imports.py example
IMPORT_MAPPINGS = {
    'from pages.': 'from ape.pages.',
    'from utils.': 'from ape.utils.',
    'from simulation_v2.': 'from simulation.',
    'import simulation_v2': 'import simulation',
    'from streamgraph_': 'from visualization.charts.streamgraph',
}

def update_file_imports(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
        content = content.replace(old_pattern, new_pattern)
    
    # Handle relative imports
    content = update_relative_imports(filepath, content)
    
    with open(filepath, 'w') as f:
        f.write(content)
```

## Benefits of Refactoring

1. **Standard Python project structure**: Easier onboarding and tooling
2. **Simplified deployment**: `streamlit run APE.py` from root
3. **Cleaner imports**: Logical module hierarchy
4. **Better code reuse**: Consolidated utilities and components
5. **Easier testing**: Single test suite location
6. **Improved CI/CD**: Standard structure for GitHub Actions
7. **Better documentation**: Clear module organization

## Streamgraph Consolidation Strategy

The repository contains 17+ different streamgraph implementations. We need to:

1. **Analyze all variants**:
   ```bash
   # List all streamgraph files
   ls streamlit_app_parquet/streamgraph_*.py
   ```

2. **Identify the best implementation**:
   - `streamgraph_patient_states_fixed.py` - Latest with fixes
   - `streamgraph_strict_conservation.py` - Ensures data conservation
   - Must preserve patient count conservation principles

3. **Merge into single module**:
   ```python
   # visualization/charts/streamgraph.py
   class StreamgraphChart:
       """Consolidated streamgraph implementation
       - Strict data conservation
       - No synthetic data generation
       - Validated against real patient counts
       """
   ```

## Scientific Validation During Refactoring

### Critical Validation Points:
1. **Data Conservation**:
   ```python
   # tests/validation/test_data_conservation.py
   def test_patient_count_conservation():
       """Ensure total patient count remains constant through transformations"""
   ```

2. **No Synthetic Data**:
   ```python
   # scripts/validate_no_synthetic.py
   def scan_for_synthetic_data_patterns():
       """Scan for forbidden patterns: 'sample', 'mock', 'fake', 'dummy'"""
   ```

3. **Simulation Reproducibility**:
   ```python
   # tests/validation/test_reproducibility.py
   def test_simulation_determinism():
       """Ensure same seed produces identical results"""
   ```

### Validation Checkpoints:
- After Phase 2: Run all scientific validation tests
- After Phase 3: Verify simulation outputs match pre-refactor
- After Phase 4: Full regression testing with saved results
- Before merge: Complete validation suite

## Risk Mitigation

1. **Preserve Git History**: 
   - Always use `git mv` instead of `mv`
   - Commit frequently with clear messages
   
2. **Maintain Backwards Compatibility**:
   ```python
   # ape/compatibility.py - Temporary shims
   import warnings
   def deprecated_import(old_path, new_path):
       warnings.warn(f"{old_path} moved to {new_path}", DeprecationWarning)
       return __import__(new_path)
   ```

3. **Incremental Testing**:
   ```bash
   # Run after each phase
   python scripts/test_runner.py --phase 1
   python scripts/validate_migration.py
   ```

4. **Scientific Integrity**:
   - Never modify simulation algorithms during move
   - Preserve all validation scripts
   - Keep debug outputs for comparison

5. **Rollback Strategy**:
   ```bash
   # If issues arise
   git checkout pre-refactor-backup
   git branch -D feature/repository-refactor
   ```

6. **Data File Handling**:
   - Keep all .parquet files in original locations initially
   - Create symlinks if needed for compatibility
   - Migrate data files only after code is stable

## Execution Timeline

1. **Week 1**: Directory structure and core file movements
2. **Week 2**: Import updates and code consolidation
3. **Week 3**: Testing and documentation updates
4. **Week 4**: Final validation and merge preparation

## Configuration Management

### Environment Configuration:
```python
# config.py at root
class Config:
    """Centralized configuration management"""
    SIMULATION_OUTPUT_DIR = "output/simulations"
    VISUALIZATION_OUTPUT_DIR = "output/visualizations"
    DEFAULT_PROTOCOL_DIR = "data/protocols"
    
    # Scientific constants
    RANDOM_SEED = 42  # For reproducibility
    CONSERVATION_TOLERANCE = 1e-10  # For validation
```

### pyproject.toml Setup:
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools-scm[toml]>=6.2"]

[project]
name = "vegf-1"
description = "AMD Treatment Simulation Platform"
requires-python = ">=3.9"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.ruff]
line-length = 88
select = ["E", "F", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

## Deployment Considerations

### Streamlit Deployment:
```yaml
# .streamlit/config.toml
[server]
port = 8502
address = "0.0.0.0"

[theme]
primaryColor = "#1f77b4"  # From color_system.py
```

### Docker Support:
```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "APE.py"]
```

### GitHub Actions Update:
```yaml
# .github/workflows/deploy.yml updates
- name: Run APE
  run: streamlit run APE.py
```

## Success Criteria

### Functional Requirements:
- [ ] APE.py runs from root directory without errors
- [ ] All existing features work identically
- [ ] Simulation results are byte-for-byte identical
- [ ] All visualizations render correctly
- [ ] R integration continues to function
- [ ] Saved simulations can be loaded

### Code Quality:
- [ ] All tests pass (unit, integration, validation)
- [ ] No circular imports
- [ ] Clean import hierarchy (no ../.. imports)
- [ ] No duplicate code remains
- [ ] Type hints preserved/added where missing
- [ ] Linting passes (black, ruff)

### Scientific Integrity:
- [ ] Patient count conservation validated
- [ ] No synthetic data generation code
- [ ] Simulation reproducibility confirmed
- [ ] Validation scripts all pass
- [ ] Debug outputs match pre-refactor

### Documentation:
- [ ] README.md updated with new structure
- [ ] CLAUDE.md updated with new paths
- [ ] API documentation generated
- [ ] Import mapping documented
- [ ] Deployment guide updated

### Performance:
- [ ] Simulation performance unchanged
- [ ] App startup time not degraded
- [ ] Memory usage consistent

### Deployment:
- [ ] CI/CD workflows function correctly
- [ ] Docker build succeeds
- [ ] Deployment simplified to single command

## Critical Do's and Don'ts

### DO:
- ✅ Use git mv to preserve history
- ✅ Test after every major change
- ✅ Keep detailed commit messages
- ✅ Validate scientific accuracy continuously
- ✅ Create backups before major operations
- ✅ Document every decision

### DON'T:
- ❌ Modify algorithms during refactoring
- ❌ Create any synthetic/sample data
- ❌ Break existing saved simulations
- ❌ Touch submodules structure
- ❌ Ignore test failures
- ❌ Rush the process

## Notes

- This refactoring maintains all existing functionality
- The `archive/` directory is temporary - remove after validation
- Consider feature flags for gradual migration
- Plan for a beta testing period before full adoption
- Keep the old structure accessible for 1-2 months

## Communication Plan

1. **Pre-refactor**: Announce plan to stakeholders
2. **During refactor**: Daily progress updates
3. **Testing phase**: Call for beta testers
4. **Post-refactor**: Migration guide for users

## Next Steps

1. Review and approve this plan
2. Create pre-refactor backup tag
3. Set up migration scripts
4. Create feature branch
5. Begin Phase 0 (analysis and tooling)
6. Execute phases with validation checkpoints
7. Beta testing period
8. Stakeholder review
9. Merge to main
10. Monitor for issues