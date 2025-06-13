# VEGF-1 Repository Refactoring Plan

## Overview
This document outlines a focused refactoring plan to extract the active application (streamlit_app_v2/APE.py) to the root level and archive historical implementations. This creates a clean, deployment-ready structure while preserving historical code for reference.

## Current State Analysis

### Repository Structure
1. **Active Application**: Only `streamlit_app_v2/APE.py` and its dependencies
2. **Historical Artifacts**: `streamlit_app/` and `streamlit_app_parquet/` (useful for archaeological reference)
3. **APE.py Location**: Currently at `streamlit_app_v2/APE.py` (needs to move to root)
4. **Simulation Engine**: `simulation_v2/` is the active version, `simulation/` is historical
5. **Mixed Active/Historical Code**: Active code intermingled with experimental versions

### Key Assets from streamlit_app_v2 to Preserve
- APE.py (main Streamlit application)
- pages/* (all Streamlit pages)
- components/* (UI components) 
- utils/* (visualization utilities, style constants)
- visualizations/* (including streamgraph_treatment_states.py)
- core/* (simulation engine)
- protocols/v2/* (YAML protocol definitions)
- simulation_results/* (saved results naming convention)
- tests/* (active test suite)
- scripts/* (development scripts)

## Target Structure

```
vegf-1/
├── APE.py                          # Main Streamlit app (moved from streamlit_app_v2/)
├── requirements.txt                # Single consolidated requirements file
├── requirements-dev.txt            # Development dependencies
├── README.md                       # Main project documentation
├── .gitignore                      # Already updated with LaTeX artifacts
├── CLAUDE.md                       # Development instructions (merge both versions)
├── pyproject.toml                  # Modern Python project config
│
├── pages/                          # Streamlit pages (from streamlit_app_v2/pages/)
│   ├── __init__.py
│   ├── 1_Protocol_Manager.py      # Protocol configuration
│   ├── 2_Run_Simulation.py        # Run simulations
│   ├── 3_Analysis.py              # Calendar-Time Analysis
│   └── 4_Patient_Explorer.py      # Individual patient view
│
├── components/                     # UI components (from streamlit_app_v2/components/)
│   ├── __init__.py
│   ├── treatment_patterns/        # Treatment pattern analysis
│   ├── economics/                 # Economic analysis components
│   └── ui_elements/               # Common UI elements
│
├── core/                          # Simulation engine (from streamlit_app_v2/core/)
│   ├── __init__.py
│   ├── abs_simulation.py          # Agent-based simulation
│   ├── des_simulation.py          # Discrete event simulation
│   ├── patient.py                 # Patient model
│   └── protocol.py                # Protocol handling
│
├── utils/                         # Utilities (from streamlit_app_v2/utils/)
│   ├── __init__.py
│   ├── chart_builder.py           # ChartBuilder pattern
│   ├── style_constants.py         # StyleConstants
│   ├── session_state.py           # Session management
│   └── visualization_modes.py     # Tufte/Presentation modes
│
├── visualizations/                # Visualization modules (from streamlit_app_v2/visualizations/)
│   ├── __init__.py
│   ├── streamgraph_treatment_states.py  # Active Plotly streamgraph
│   ├── streamgraph_comprehensive.py     # Comprehensive analysis
│   └── economic_charts.py              # Economic visualizations
│
├── protocols/                     # Protocol definitions
│   └── v2/                       # YAML protocols (from streamlit_app_v2/protocols/v2/)
│       ├── aflibercept_pro.yaml
│       ├── aflibercept_te.yaml
│       └── ...
│
├── simulation_results/            # Saved simulations (preserve naming convention)
│   └── YYYYMMDD-HHMMSS-sim-Xp-Yy.parquet
│
├── tests/                         # Active tests (from streamlit_app_v2/tests/)
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── ui/                       # Playwright tests
│
├── scripts/                       # Development scripts (from streamlit_app_v2/scripts/)
│   ├── run_tests.py
│   ├── dev_setup.sh
│   └── run_baseline_tests.sh
│
├── validation/                    # Scientific validation (keep at root)
│   ├── verify_fixed_discontinuation.py
│   ├── verify_streamlit_integration.py
│   └── ...
│
├── visualization/                 # Shared visualization (already at root)
│   └── color_system.py           # Central color system
│
├── meta/                         # Project insights (preserved)
│   ├── visualization_templates.md
│   ├── streamgraph_synthetic_data_postmortem.md
│   └── ...
│
├── output/                       # Generated outputs (gitignored)
│   ├── simulations/
│   ├── visualizations/
│   └── debug/
│
├── docs/                         # Documentation
│   ├── api/
│   ├── user_guide/
│   └── development/
│
├── archive/                      # Historical code (for archaeological reference)
│   ├── streamlit_app/           # Old Streamlit app
│   ├── streamlit_app_parquet/   # Parquet experiments
│   ├── simulation/              # Old simulation engine
│   └── README.md               # Explain archive contents
│
├── Paper/                       # Academic paper (unchanged)
├── designer/                    # Design tools (unchanged)
├── mcp/                        # MCP servers (unchanged)
│
# Submodules remain at root level
├── aflibercept_2mg_data/       # Git submodule
├── eylea_high_dose_data/       # Git submodule
└── vegf_literature_data/       # Git submodule
```

## Refactoring Steps

### Phase 0: Pre-refactoring Analysis
1. **Analyze streamlit_app_v2 structure**:
   ```bash
   # Map all imports in the active app
   grep -r "^from\|^import" streamlit_app_v2/ --include="*.py" > v2_imports.txt
   
   # Check for any dependencies on other apps
   grep -r "streamlit_app\." streamlit_app_v2/ --include="*.py"
   grep -r "streamlit_app_parquet\." streamlit_app_v2/ --include="*.py"
   ```

2. **Create backup tag**:
   ```bash
   git tag pre-refactor-backup
   ```

### Phase 1: Create New Branch and Structure
```bash
git checkout -b feature/repository-refactor

# Create archive directory
mkdir -p archive

# Create output directories (for gitignore)
mkdir -p output/{simulations,visualizations,debug}

# Documentation structure
mkdir -p docs/{user_guide,development,api}
```

### Phase 2: Extract Active Application (streamlit_app_v2)
1. **Move APE.py to root**:
   ```bash
   git mv streamlit_app_v2/APE.py ./
   ```

2. **Move application directories to root**:
   ```bash
   # Move all active directories
   git mv streamlit_app_v2/pages ./
   git mv streamlit_app_v2/components ./
   git mv streamlit_app_v2/core ./
   git mv streamlit_app_v2/utils ./
   git mv streamlit_app_v2/visualizations ./
   git mv streamlit_app_v2/protocols ./
   git mv streamlit_app_v2/tests ./
   git mv streamlit_app_v2/scripts ./
   
   # Move simulation results directory
   git mv streamlit_app_v2/simulation_results ./
   ```

3. **Merge CLAUDE.md files**:
   ```bash
   # Combine root and app-specific CLAUDE.md
   cat streamlit_app_v2/CLAUDE.md >> CLAUDE.md
   echo "\n# === Merged from streamlit_app_v2 ===\n" >> CLAUDE.md
   ```

4. **Move other v2-specific files**:
   ```bash
   # Move any v2-specific configs
   git mv streamlit_app_v2/.streamlit ./ 2>/dev/null || true
   git mv streamlit_app_v2/requirements.txt ./requirements-v2.txt
   ```

### Phase 3: Archive Historical Code
```bash
# Archive old apps
git mv streamlit_app archive/
git mv streamlit_app_parquet archive/
git mv simulation archive/
git mv streamlit_app_v2 archive/  # Archive the now-empty directory

# Create archive README
cat > archive/README.md << 'EOF'
# Historical Code Archive

This directory contains historical implementations preserved for archaeological reference.

## Contents

- `streamlit_app/` - Original Streamlit application
- `streamlit_app_parquet/` - Experimental Parquet-based implementation with 17+ streamgraph variants
- `simulation/` - Original simulation engine (replaced by simulation_v2)
- `streamlit_app_v2/` - Empty directory structure after extraction to root

## Note

The active application has been extracted to the root directory. These archives are maintained for:
- Historical reference
- Understanding evolution of the codebase
- Retrieving specific implementations if needed

For the active application, see APE.py in the root directory.
EOF

git add archive/README.md
```

### Phase 4: Update Imports

Since we're moving directories to root level, most imports will actually become simpler:

```python
# Current imports in streamlit_app_v2 files:
from pages.simulation import simulation_page
from utils.session_state import init_session_state
from core.abs_simulation import ABSSimulation
from visualizations.streamgraph_treatment_states import create_treatment_state_streamgraph

# After refactoring (no change needed!):
from pages.simulation import simulation_page
from utils.session_state import init_session_state
from core.abs_simulation import ABSSimulation
from visualizations.streamgraph_treatment_states import create_treatment_state_streamgraph
```

**Key insight**: Since we're moving streamlit_app_v2 contents to root, internal imports don't need to change!

### Phase 5: Handle External Dependencies

1. **Check for dependencies on archived code**:
   ```bash
   # Find any imports from old apps
   grep -r "from streamlit_app\." . --include="*.py" --exclude-dir=archive
   grep -r "import streamlit_app\." . --include="*.py" --exclude-dir=archive
   ```

2. **Update visualization imports**:
   ```python
   # The central color system import stays the same:
   from visualization.color_system import COLORS
   ```

3. **Update any simulation_v2 references**:
   ```bash
   # Since simulation_v2 is now just 'core' at root
   # No changes needed - core is already at the right level
   ```

### Phase 6: Validation and Testing

1. **Test the refactored structure**:
   ```bash
   # Run the app from root
   streamlit run APE.py
   
   # Run test suite
   python scripts/run_tests.py --all
   ```

2. **Verify imports**:
   ```python
   # scripts/verify_imports.py
   import ast
   import os
   
   def verify_no_missing_imports(directory):
       """Check all Python files for import errors"""
       for root, dirs, files in os.walk(directory):
           if 'archive' in root:
               continue
           for file in files:
               if file.endswith('.py'):
                   # Try to parse the file
                   filepath = os.path.join(root, file)
                   try:
                       with open(filepath, 'r') as f:
                           ast.parse(f.read())
                   except SyntaxError as e:
                       print(f"Syntax error in {filepath}: {e}")
   ```

## Import Path Mapping

| Old Path | New Path | Notes |
|----------|----------|-------|
| `streamlit_app_v2/APE.py` | `APE.py` | Main app at root |
| `streamlit_app_v2/pages/*` | `pages/*` | No import changes needed |
| `streamlit_app_v2/utils/*` | `utils/*` | No import changes needed |
| `streamlit_app_v2/components/*` | `components/*` | No import changes needed |
| `streamlit_app_v2/core/*` | `core/*` | No import changes needed |
| `streamlit_app_v2/visualizations/*` | `visualizations/*` | No import changes needed |
| `streamlit_app_v2/protocols/v2/*` | `protocols/v2/*` | No import changes needed |
| `visualization/color_system.py` | `visualization/color_system.py` | Already at root |
| `validation/*.py` | `validation/*.py` | Already at root |

**Key Insight**: Since we're lifting streamlit_app_v2 to root, most imports remain unchanged!

## Simplified Import Strategy

Since we're moving entire directory structure from `streamlit_app_v2/` to root:

1. **No import changes needed within the app** - All relative imports stay the same
2. **Only external references need updates** - References from validation scripts, etc.
3. **Archive imports should fail** - This is good, ensures clean separation

```python
# Example: No changes needed in these imports
from pages.1_Protocol_Manager import protocol_manager_page  # Works before and after
from utils.chart_builder import ChartBuilder  # Works before and after
from core.des_simulation import DESSimulation  # Works before and after
```

## Benefits of Refactoring

1. **Standard Python project structure**: Easier onboarding and tooling
2. **Simplified deployment**: `streamlit run APE.py` from root
3. **Cleaner imports**: Logical module hierarchy
4. **Better code reuse**: Consolidated utilities and components
5. **Easier testing**: Single test suite location
6. **Improved CI/CD**: Standard structure for GitHub Actions
7. **Better documentation**: Clear module organization

## Key Simplifications

### No Streamgraph Consolidation Needed!

Since only `streamlit_app_v2` is active:
- **Active streamgraph**: `visualizations/streamgraph_treatment_states.py` (Plotly-based)
- **No consolidation required**: The 17+ variants in streamlit_app_parquet are historical
- **Archive contains experiments**: Useful for archaeological reference only

### Minimal Code Changes

The refactoring is much simpler than originally planned:
1. **Lift and shift**: Move streamlit_app_v2 contents to root
2. **Archive historical code**: Move old apps to archive/
3. **No import updates needed**: Internal app imports remain the same
4. **No merge conflicts**: Only one active implementation

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

### Simplified Timeline (1-2 weeks total)

1. **Day 1-2**: 
   - Create branch and backup
   - Move streamlit_app_v2 contents to root
   - Archive historical code

2. **Day 3-4**:
   - Test application from root
   - Update external references (validation scripts)
   - Merge CLAUDE.md files

3. **Day 5-7**:
   - Full test suite validation
   - Update documentation
   - Create deployment branch

4. **Week 2**:
   - Beta testing period
   - Fix any issues
   - Merge to main

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

### Simplified Criteria

#### Must Have:
- [ ] `streamlit run APE.py` works from root directory
- [ ] All simulation features work identically
- [ ] Test suite passes: `python scripts/run_tests.py --all`
- [ ] Validation scripts work with new structure
- [ ] Historical code properly archived

#### Should Have:
- [ ] CLAUDE.md merged and updated
- [ ] Clean directory structure at root
- [ ] No references to archived code from active code
- [ ] Documentation reflects new structure

#### Nice to Have:
- [ ] Docker configuration updated
- [ ] CI/CD simplified
- [ ] Deployment branch created

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

## Summary of Changes

This refactoring plan has been significantly simplified based on the understanding that:

1. **Only streamlit_app_v2 is active** - Other apps are historical artifacts
2. **No complex consolidation needed** - Just lift and shift v2 to root
3. **Minimal import changes** - Internal app imports stay the same
4. **Clear separation** - Active code at root, historical in archive/

The refactoring becomes a straightforward extraction rather than a complex merge.

## Next Steps

1. Review this simplified plan
2. Create feature branch: `git checkout -b feature/repository-refactor`
3. Execute Phase 1-6 (should take 1-2 weeks)
4. Test thoroughly
5. Create deployment branch for production use
6. Merge to main after validation