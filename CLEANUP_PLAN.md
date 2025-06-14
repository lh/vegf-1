# APE Codebase Cleanup Plan

## Current State (Deployment Branch)
- Main app: APE.py
- Pages: pages/*.py
- Core logic: ape/
- Legacy directories: streamlit_app/, streamlit_app_parquet/, streamlit_app_v2/
- Some visualization/ files still import from streamlit_app/

## Cleanup Steps

### 1. Fix Remaining Imports
Update these files to use ape/utils/tufte_zoom_style.py instead of streamlit_app.utils.tufte_style:
- [ ] visualization/visualization_templates.py
- [ ] visualization/discontinuation_chart.py  
- [ ] visualization/nested_bar_chart.py

### 2. Archive Legacy Directories
```bash
mkdir -p archive/legacy_streamlit_apps
mv streamlit_app archive/legacy_streamlit_apps/
mv streamlit_app_parquet archive/legacy_streamlit_apps/
mv streamlit_app_v2 archive/legacy_streamlit_apps/
```

### 3. Consolidate Workload Visualizations
Merge into ONE file: ape/components/treatment_patterns/workload_visualizations.py
- [ ] Merge regular, optimized, and altair versions
- [ ] Use feature flags for switching implementations
- [ ] Delete duplicate files

### 4. Fix Clinical Workload Analysis
In pages/3_Analysis.py:
- [ ] Import from consolidated workload visualization
- [ ] Remove fallback imports
- [ ] Use feature flags for Altair vs Plotly

### 5. Clean Deployment Process
- [ ] Merge deployment branch back to main
- [ ] Delete deployment branch
- [ ] Deploy only from main branch
- [ ] Document in DEPLOYMENT.md

### 6. Update Documentation
Create/Update:
- [ ] CLAUDE.md with clear structure rules
- [ ] DEPLOYMENT.md with deployment process
- [ ] README.md to reflect current structure

## Final Structure
```
/
├── APE.py                    # Main entry point
├── pages/                    # Streamlit pages
│   ├── 1_Protocol_Manager.py
│   ├── 2_Simulations.py
│   └── 3_Analysis.py
├── ape/                      # Core application
│   ├── components/
│   ├── utils/
│   └── simulation/
├── visualization/            # Standalone viz tools
├── protocols/               # Protocol definitions
├── archive/                 # Old code for reference
│   └── legacy_streamlit_apps/
├── .streamlit/
├── requirements.txt
└── *.md                     # Documentation
```

## Deployment Configuration
Use .streamlit/secrets.toml for feature flags:
```toml
# Development
ENABLE_ALTAIR_CHARTS = true
DEBUG_MODE = true

# Production  
ENABLE_ALTAIR_CHARTS = false
DEBUG_MODE = false
```