# VEGF-1 Repository Refactoring Plan - Streamlit Compliant Version

## Overview
This plan refactors the VEGF-1 repository for easy deployment while maintaining full Streamlit compatibility. The functional app in `streamlit_app_v2` will be extracted to the root level with a clean structure.

## Core Principles
1. **Streamlit Compliance** - Pages MUST be in root `pages/` directory
2. **Easy Deployment** - Single command: `streamlit run APE.py`
3. **Clean Separation** - Production vs Development code
4. **No Path Hacks** - Clean imports without sys.path manipulation
5. **Preserve Everything** - All development tools remain accessible

## Target Structure

```
vegf-1/
# PRODUCTION DEPLOYMENT (What gets deployed)
├── APE.py                          # Main entry point (from streamlit_app_v2/)
├── pages/                          # Streamlit pages (REQUIRED location)
│   ├── 1_Protocol_Manager.py      # Production pages only
│   ├── 2_Simulations.py
│   └── 3_Analysis.py
├── ape/                           # Core application modules
│   ├── components/                # UI components
│   ├── core/                      # Simulation engine
│   ├── utils/                     # Application utilities
│   ├── visualizations/            # Visualization modules
│   └── protocols/                 # Protocol definitions
├── assets/                        # Static assets (logo, images)
├── protocols/                     # Protocol YAML files (root level)
├── simulation_results/            # Saved simulation outputs
├── .streamlit/                    # Streamlit configuration
├── requirements.txt               # Production dependencies only
└── README.md                      # User documentation

# DEVELOPMENT ENVIRONMENT (Excluded from deployment)
├── dev/                          # All development-only code
│   ├── pages/                    # Debug/experimental pages
│   │   ├── 98_Debug_Environment.py
│   │   ├── 99_Carbon_Button_Test.py
│   │   └── 4_Experiments.py     # Non-production pages
│   ├── experiments/              # From streamlit_app_v2/experiments/
│   ├── test_scripts/             # Testing utilities
│   ├── migration/                # Refactoring tools
│   └── benchmarks/               # Performance testing
│
├── streamlit_app_v2/             # TO BE ARCHIVED after extraction
│   ├── tests/                    # Move to root tests/
│   ├── scripts/                  # Move to root scripts/
│   └── [remaining structure]     # Archive after verification
│
├── tests/                        # Test suite (from streamlit_app_v2/)
├── scripts/                      # Dev scripts (from streamlit_app_v2/)
├── visualization/                # Central color system (existing)
├── validation/                   # Scientific validation (existing)
│
├── literature_extraction/        # Parameter extraction (existing)
│   ├── aflibercept_2mg_data/
│   ├── eylea_high_dose_data/
│   └── vegf_literature_data/
│
├── archive/                      # Historical implementations
│   ├── streamlit_app/           # Old version
│   ├── streamlit_app_parquet/   # Parquet version
│   └── streamlit_app_v2/        # After extraction complete
│
├── docs/                        # Documentation
├── meta/                        # Project insights
├── Paper/                       # Academic paper
├── reports/                     # Generated reports
├── requirements-dev.txt         # Development dependencies
├── CLAUDE.md                    # AI instructions
└── pyproject.toml              # Python project config
```

## Import Structure

Production code uses clean imports:
```python
# In APE.py
from ape.utils.carbon_button_helpers import navigation_button

# In pages/1_Protocol_Manager.py
from ape.core.simulation_runner import SimulationRunner
from ape.components.simulation_ui import render_simulation_form

# In ape/components/some_component.py
from ape.utils.style_constants import StyleConstants
from ape.core.results import SimulationResults
```

## Implementation Progress Tracker

### ✅ COMPLETED
- [x] Created feature branch: `refactor/deployment-structure`
- [x] Created backup tag: `pre-refactor-backup`
- [x] Dependency analysis completed (no circular dependencies found)
- [x] Created migration tools directory: `dev/migration/`
- [x] Moved APE.py from streamlit_app_v2/ to root
- [x] Created ape/ directory structure
- [x] Moved core modules to ape/:
  - [x] components/ → ape/components/
  - [x] core/ → ape/core/
  - [x] utils/ → ape/utils/
  - [x] visualizations/ → ape/visualizations/
  - [x] protocols/ → ape/protocols/
- [x] Moved assets/ to root
- [x] Created simulation_results/ directory
- [x] Moved pages/ to root (Streamlit requirement)
- [x] Fixed imports in all moved files (ape. prefix)
- [x] Moved debug pages to dev/pages/
- [x] Moved experiments/ to dev/experiments/
- [x] Moved streamlit_app_v2/tests/ to tests_v2/
- [x] Moved streamlit_app_v2/scripts/ to scripts_v2/
- [x] Created requirements.txt (production only)
- [x] Created requirements-dev.txt
- [x] Removed sys.path hacks from pages
- [x] Basic application test - APE.py runs successfully

### ✅ RECENTLY COMPLETED
- [x] Full application functionality testing
- [x] Archive streamlit_app_v2/
- [x] Update main README.md for new structure
- [x] Validate scientific computations
- [x] Root directory cleanup (~400 files organized)
- [x] Created WHERE_TO_PUT_THINGS.md guide
- [x] Git worktree strategy documentation

### ✅ PREVIOUSLY COMPLETED
- [x] Merged tests_v2 with existing tests/
- [x] Renamed scripts_v2 to scripts/
- [x] Created deployment guide (DEPLOYMENT_GUIDE.md)
- [x] Created Docker configuration (Dockerfile, .dockerignore)
- [x] Created deployment checklist (DEPLOYMENT_CHECKLIST.md)
- [x] Updated pre-commit hooks for new structure

### ✅ ALL TASKS COMPLETED!

The refactoring is now complete. The VEGF-1 repository has been successfully transformed into a clean, deployable structure while maintaining all development capabilities.

## Deployment Strategy

### Local Development
```bash
pip install -r requirements-dev.txt
streamlit run APE.py
```

### Production Deployment
```bash
pip install -r requirements.txt
streamlit run APE.py --server.port 80 --server.maxUploadSize 1000
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY APE.py .
COPY pages/ ./pages/
COPY ape/ ./ape/
COPY assets/ ./assets/
COPY protocols/ ./protocols/
COPY .streamlit/ ./.streamlit/
CMD ["streamlit", "run", "APE.py", "--server.port=8501"]
```

### What to Exclude in Deployment
- dev/
- archive/
- literature_extraction/
- tests/
- scripts/
- All .md files except README.md
- requirements-dev.txt
- pyproject.toml
- Any __pycache__ directories
- .git/
- node_modules/

## Success Criteria
- [ ] `streamlit run APE.py` works without errors
- [ ] All production pages load correctly
- [ ] No sys.path manipulations in production code
- [ ] Clean imports using ape. prefix
- [ ] Debug pages accessible via `streamlit run dev/pages/99_*.py`
- [ ] All tests pass
- [ ] Docker build succeeds
- [ ] Deployment package < 100MB