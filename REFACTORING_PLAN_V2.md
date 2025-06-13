# VEGF-1 Repository Refactoring Plan V2

## Overview
This refactoring separates three distinct systems:
1. **APE Simulation Platform** - Core deployment application
2. **Clinical Data Analysis** - Real-world data tools (for separate repository)
3. **Literature Extraction** - Parameter extraction tools (keep but exclude from deployment)

## Target Structure

```
vegf-1/
├── APE.py                          # Main app (from streamlit_app_v2/)
├── requirements.txt                # Core dependencies
├── requirements-dev.txt            # Development dependencies
├── README.md                       # Project documentation
├── CLAUDE.md                       # Development instructions
├── .gitignore
├── pyproject.toml                  # Modern Python config
│
# Core APE Application (from streamlit_app_v2/)
├── pages/                          # Streamlit pages
├── components/                     # UI components
├── core/                          # Simulation engine
├── utils/                         # Application utilities
├── visualizations/                # Visualization modules
├── protocols/                     # Protocol definitions
├── simulation_results/            # Results directory
├── assets/                        # Static assets
├── .streamlit/                    # Streamlit config
│
# Shared Infrastructure (already at root)
├── visualization/                 # Central color system
│   └── color_system.py
├── validation/                    # Scientific validation
│   └── verify_*.py
│
# Development Tools (exclude from deployment)
├── literature_extraction/         # Parameter extraction
│   ├── aflibercept_2mg_data/    # Submodule
│   ├── eylea_high_dose_data/    # Submodule
│   ├── vegf_literature_data/    # Submodule
│   ├── scripts/                 # Extraction scripts
│   │   ├── extract_literature_data.py
│   │   ├── extract_baseline_va.py
│   │   └── ...
│   └── README.md
│
├── development/                  # Development-only tools
│   ├── experiments/             # From streamlit_app_v2/experiments/
│   ├── debug_pages/             # Debug pages (98_, 99_)
│   ├── test_scripts/            # Test infrastructure
│   └── README.md
│
├── clinical_analysis/           # To be moved to separate repo
│   ├── analysis/               # From /analysis/
│   ├── scripts/                # analyze_*.py scripts
│   └── MIGRATION_NOTES.md
│
├── tests/                      # Test suite (from streamlit_app_v2/tests/)
├── scripts/                    # Dev scripts (from streamlit_app_v2/scripts/)
├── docs/                       # Documentation
├── output/                     # Generated outputs (gitignored)
│
├── archive/                    # Historical code
│   ├── streamlit_app/
│   ├── streamlit_app_parquet/
│   ├── simulation/            # Old simulation engine
│   └── README.md
│
# Existing directories (unchanged)
├── Paper/                     # Academic paper
├── reports/                   # Generated reports
├── examples/                  # Example code
├── designer/                  # Design tools
├── mcp/                      # MCP servers
├── meta/                     # Project insights
└── notebooks/                # Jupyter notebooks
```

## Refactoring Phases

### Phase 1: Prepare Structure (Day 1)
1. Create feature branch
2. Create new directories
3. Prepare migration scripts

### Phase 2: Extract Core APE (Day 2)
1. Move streamlit_app_v2 contents to root
2. Update imports if needed
3. Test application

### Phase 3: Organize Development Tools (Day 3)
1. Create literature_extraction directory
2. Move extraction scripts
3. Create development directory
4. Move experiments and debug tools

### Phase 4: Separate Clinical Analysis (Day 4)
1. Create clinical_analysis directory
2. Move analysis tools
3. Document migration plan
4. Create separate repository

### Phase 5: Archive Historical Code (Day 5)
1. Move old apps to archive
2. Clean up root directory
3. Update documentation

### Phase 6: Validation & Testing (Days 6-7)
1. Run full test suite
2. Validate all three systems
3. Update documentation
4. Create deployment branch

## Deployment Strategy

### Production Branch Exclusions
```gitignore
# Exclude from deployment
/archive/
/clinical_analysis/
/literature_extraction/
/development/
/notebooks/
**/debug_*.py
**/test_*.py
**/*_test.py
```

### Three Repository Structure

1. **vegf-1** (Main Repository)
   - APE simulation platform
   - Public/open source
   - Deployment ready

2. **vegf-clinical-analysis** (New Repository)
   - Real-world data analysis
   - Private/restricted access
   - On-premises deployment

3. **vegf-1** (Keep Literature Tools)
   - Literature extraction stays in main
   - Excluded from production
   - Used for parameter development

## Success Criteria

- [ ] APE runs from root: `streamlit run APE.py`
- [ ] Clinical analysis tools organized separately
- [ ] Literature extraction tools organized but functional
- [ ] All tests pass
- [ ] Clean separation between systems
- [ ] Deployment branch contains only APE core