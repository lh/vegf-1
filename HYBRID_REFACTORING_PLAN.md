# Hybrid Repository Refactoring Plan

## Executive Summary

This plan outlines the reorganization of the main branch to adopt a hybrid repository structure that:
1. Maintains a clean deployment area matching the deployment branch
2. Preserves all research, analysis, and paper work in organized directories
3. Consolidates scattered tests and documentation
4. Uses configuration (not branches) for deployment differences

## Current State Analysis

### Main Branch Contents
- **Deployment Code**: APE.py, pages/, ape/, protocols/, visualization/
- **Legacy Apps**: streamlit_app/, streamlit_app_parquet/, streamlit_app_v2/ (in archive/)
- **Research/Analysis**: 
  - Real data analysis scripts in analysis/
  - Experimental code in dev/experiments/
  - Test scripts in dev/test_scripts/
- **Paper**: Paper/medical-computing-paper/
- **Documentation**: 
  - Current: docs/, meta/, various .md files in root
  - Outdated: Many files need archiving
- **Tests**: Scattered in tests/, dev/test_scripts/, individual test files in root

### Deployment Branch State
- Clean structure with only deployment-necessary files
- 726 files removed compared to main
- Working Altair implementation (though aesthetically needs work)
- No research/analysis/paper content

## Proposed Hybrid Structure

```
vegf-1/
├── APE.py                    # Main app entry
├── pages/                    # Streamlit pages
├── ape/                      # Core application modules
├── protocols/                # Treatment protocols
├── visualization/            # Visualization modules
├── assets/                   # Images and static files
├── requirements.txt          # Production dependencies
├── .streamlit/              # Streamlit config
├── .streamlitignore         # NEW: Deployment exclusions
│
├── archive/                 # Historical/deprecated code
│   ├── legacy_apps/         # Old streamlit implementations
│   ├── old_docs/            # Outdated documentation
│   └── README.md            # Explains archive contents
│
├── research/                # Active non-deployed work
│   ├── data_analysis/       # Real patient data analysis
│   ├── experiments/         # Prototype features
│   ├── test_scripts/        # Development utilities
│   └── README.md            # Research directory guide
│
├── paper/                   # Academic paper work
│   ├── medical-computing-paper/
│   └── README.md
│
├── tests/                   # All tests consolidated
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── README.md
│
├── docs/                    # Current documentation
│   ├── deployment/
│   ├── development/
│   └── api/
│
└── meta/                    # Project metadata
    ├── planning/
    ├── design_decisions/
    └── postmortems/
```

## Implementation Steps

### Phase 1: Create Directory Structure
```bash
# Create new directories
mkdir -p archive/{legacy_apps,old_docs}
mkdir -p research/{data_analysis,experiments,test_scripts}
mkdir -p tests/{unit,integration,regression}
mkdir -p docs/{deployment,development,api}
```

### Phase 2: Move Files (Organized by Category)

#### 2.1 Archive Legacy Apps
```bash
# Already in archive on main
# Verify: archive/streamlit_app_v2/
```

#### 2.2 Move Research/Analysis
```bash
# Real data analysis
mv analysis/*.py research/data_analysis/
mv aflibercept_2mg_data/ research/data_analysis/
mv eylea_high_dose_data/ research/data_analysis/
mv vegf_literature_data/ research/data_analysis/

# Experiments
mv dev/experiments/* research/experiments/
mv scratchpad/* research/experiments/scratchpad/

# Test scripts
mv dev/test_scripts/* research/test_scripts/
```

#### 2.3 Consolidate Tests
```bash
# Find and move all test files
find . -name "*test*.py" -type f | grep -v ".git" | xargs -I {} mv {} tests/
find . -name "test_*.py" -type f | grep -v ".git" | xargs -I {} mv {} tests/

# Organize by type (manual sorting needed)
# Unit tests → tests/unit/
# Integration tests → tests/integration/
# Regression tests → tests/regression/
```

#### 2.4 Organize Documentation
```bash
# Archive old docs
mv *_SUMMARY.md archive/old_docs/
mv *_PLAN.md archive/old_docs/
mv *_FIX*.md archive/old_docs/

# Keep current deployment docs
mv DEPLOYMENT*.md docs/deployment/
mv WHERE_TO_PUT_THINGS.md docs/development/
```

### Phase 3: Create .streamlitignore
```
# Research and development
archive/
research/
paper/
tests/
meta/

# Development files
*.test.py
*_test.py
test_*.py
.pytest_cache/
.coverage

# Documentation
docs/
*.md
!README.md

# Version control
.git/
.github/
.gitignore
.gitmodules

# Python
__pycache__/
*.pyc
.env
.venv/
venv/

# OS
.DS_Store
Thumbs.db

# Development tools
.vscode/
.idea/
*.swp
*.swo

# Logs and temp
*.log
temp/
tmp/
output/
simulation_results/
```

### Phase 4: Clean Root Directory

Move to appropriate locations:
- Development scripts → research/test_scripts/
- Old plans/summaries → archive/old_docs/
- Current guides → docs/

Keep in root only:
- APE.py (main entry)
- requirements.txt
- README.md
- CLAUDE.md
- Configuration files (.gitignore, etc.)

### Phase 5: Update Import Paths

After reorganization, update any imports that reference moved files:
1. Check visualization/ imports
2. Update test imports
3. Fix any research script dependencies

### Phase 6: Merge Deployment Improvements

```bash
# Bring in Altair and other fixes from deployment
git checkout deployment -- ape/components/treatment_patterns/workload_visualizations_altair.py
git checkout deployment -- visualization/__init__.py
```

## Benefits of This Approach

1. **Clean Deployment**: Streamlit only sees production code
2. **Preserved Research**: All analysis work remains accessible
3. **Single Repository**: No juggling multiple repos
4. **Clear Organization**: Obvious where everything belongs
5. **Easy Promotion**: Move research/ → production when ready
6. **Version Control**: Full history preserved

## Migration Checklist

- [ ] Create directory structure
- [ ] Move legacy apps to archive/
- [ ] Move research/analysis files
- [ ] Consolidate all tests
- [ ] Organize documentation
- [ ] Create .streamlitignore
- [ ] Clean root directory
- [ ] Update imports
- [ ] Test deployment locally
- [ ] Document new structure in README

## Post-Migration

1. Delete deployment branch (main becomes source of truth)
2. Configure Streamlit Cloud to deploy from main
3. Use environment variables for any deployment-specific settings
4. Regular maintenance: archive old files, promote stable research

## Risk Mitigation

1. **Backup First**: Create main-backup-YYYYMMDD branch
2. **Test Locally**: Ensure app runs after each major move
3. **Gradual Migration**: Can be done in phases
4. **Revertible**: Git history preserves everything

## Success Criteria

- [ ] Main branch deploys cleanly to Streamlit Cloud
- [ ] All research/analysis work accessible in organized folders
- [ ] No duplicate files or scattered tests
- [ ] Clear documentation of new structure
- [ ] Deployment issues (entry point, Altair) documented for future fix