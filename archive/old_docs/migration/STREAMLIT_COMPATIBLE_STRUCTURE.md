# Streamlit-Compatible Refactoring Structure

## The Issue
The original refactoring plan suggests `ape/pages/`, but Streamlit REQUIRES pages to be in a `pages/` directory at the root level (relative to the main script).

## Solution: Hybrid Approach

Keep the core of the refactoring plan but adjust for Streamlit's requirements:

```
vegf-1/
# DEPLOYMENT CORE
├── APE.py                          # Main entry (from streamlit_app_v2/APE.py)
├── pages/                          # Production pages (MUST be here for Streamlit)
│   ├── 1_Protocol_Manager.py      
│   ├── 2_Simulations.py
│   └── 3_Analysis.py
├── ape/                           # Core modules (as planned)
│   ├── components/                # UI components
│   ├── core/                      # Simulation engine
│   ├── utils/                     # Application utilities
│   ├── visualizations/            # Visualization modules
│   └── protocols/                 # Protocol definitions
├── assets/                        # Static assets
├── simulation_results/            # Results directory
├── .streamlit/                    # Streamlit config
├── requirements.txt               # Production dependencies

# DEVELOPMENT LAYER
├── dev/
│   ├── pages/                    # Debug pages (moved from pages/)
│   │   ├── 98_Debug_Environment.py
│   │   └── 99_Carbon_Button_Test.py
│   ├── experiments/              # From streamlit_app_v2/experiments/
│   ├── test_scripts/             # Testing utilities
│   └── migration/                # Our current work
│
├── streamlit_app_v2/             # Keep for now, archive later
│   ├── tests/                    # Move to tests/ at root
│   ├── scripts/                  # Move to scripts/ at root
│   └── ...                       # Archive remaining structure
│
└── [rest as per original plan]
```

## Next Steps

1. **Move debug pages to dev/**
   ```bash
   mkdir -p dev/pages
   git mv pages/98_*.py dev/pages/
   git mv pages/99_*.py dev/pages/
   ```

2. **Move remaining streamlit_app_v2 items**
   - tests/ → root tests/
   - scripts/ → root scripts/
   - experiments/ → dev/experiments/

3. **Update imports in pages/**
   - Change from `from components` to `from ape.components`
   - Change from `from core` to `from ape.core`

4. **Archive streamlit_app_v2/**
   - After everything is moved and working

## Benefits
- ✅ Streamlit compatible (pages at root)
- ✅ Clean separation (ape/ for core modules)
- ✅ Development tools isolated (dev/)
- ✅ Easy deployment (exclude dev/, archive/, etc.)
- ✅ Follows the spirit of the original plan