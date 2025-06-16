# Active Instructions

**IMPORTANT**: This is the primary instruction file. Always check this file at the start of each session.

## 🚨 Current Active Task: Time-Based Disease Model Implementation
**Status**: Implementation Starting  
**Branch**: feature/time-based-disease-model  
**Instructions**: See TIME_BASED_IMPLEMENTATION_INSTRUCTIONS.md

### Previous Task: Hybrid Repository Refactoring ✅
**Status**: COMPLETE (Phases 1-5 done, deployment testing pending)  
**Branch**: main  
**Backup**: main-backup-20250114  

## Overview

We are reorganizing the repository from a messy main branch into a clean hybrid structure that:
1. Maintains clean deployment code matching the deployment branch
2. Preserves all research, analysis, and paper work in organized directories  
3. Uses .streamlitignore for deployment control
4. Consolidates scattered tests and documentation

## Directory Structure

```
vegf-1/
├── APE.py                    # Main app entry (DEPLOYED)
├── pages/                    # Streamlit pages (DEPLOYED)
├── ape/                      # Core modules (DEPLOYED)
├── protocols/                # Treatment protocols (DEPLOYED)
├── visualization/            # Visualization modules (DEPLOYED)
├── assets/                   # Static files (DEPLOYED)
├── requirements.txt          # Production dependencies (DEPLOYED)
├── .streamlit/              # Streamlit config (DEPLOYED)
├── .streamlitignore         # NEW: Deployment exclusions
│
├── archive/                 # NOT DEPLOYED - Historical code
│   ├── legacy_apps/         # Old streamlit implementations
│   ├── old_docs/            # Outdated documentation
│   └── README.md
│
├── research/                # NOT DEPLOYED - Active development
│   ├── data_analysis/       # Real patient data analysis
│   ├── experiments/         # Prototype features
│   ├── test_scripts/        # Development utilities
│   └── README.md
│
├── paper/                   # NOT DEPLOYED - Academic paper
│   └── medical-computing-paper/
│
├── tests/                   # NOT DEPLOYED - All tests
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

## Implementation Phases

### ✅ Phase 0: Preparation (COMPLETE)
- [x] Create backup branch: main-backup-20250114
- [x] Disable pre-commit hook temporarily
- [x] Document plan in HYBRID_REFACTORING_PLAN.md
- [x] Create FILE_MIGRATION_MAP.md

### ✅ Phase 1: Create Directory Structure (COMPLETE)
- [x] Create archive/{legacy_apps,old_docs}
- [x] Create research/{data_analysis,experiments,test_scripts}
- [x] Create tests/{unit,integration,regression}
- [x] Create docs/{deployment,development,api}
- [x] Create README.md files for each major directory

### ✅ Phase 2: Move Files (COMPLETE)
Follow FILE_MIGRATION_MAP.md to move:
- [x] Archive old summaries and reports
- [x] Move research/analysis files  
- [x] Move experimental code
- [x] Consolidate all tests
- [x] Organize documentation

### ✅ Phase 3: Create .streamlitignore (COMPLETE)
- [x] Create comprehensive .streamlitignore file
- [ ] Test deployment exclusions work

### ✅ Phase 4: Clean Root Directory (COMPLETE)
- [x] Ensure root has only essential files
- [x] Update any broken imports (fixed visualization/__init__.py)
- [x] Test application still runs (verified with streamlit run APE.py)

### ✅ Phase 5: Merge Deployment Improvements (COMPLETE)
- [x] Bring in Altair fixes from deployment branch
- [x] Import workload_visualizations_altair.py
- [x] Update enhanced_tab.py to force Altair usage
- [x] Update pages/3_Analysis.py to use Altair
- [x] Document known issues (entry point, Altair aesthetics) in DEPLOYMENT_ISSUES_20250114.md

### ⏳ Phase 6: Final Testing & Cleanup
- [ ] Test local deployment
- [ ] Re-enable pre-commit hook
- [ ] Update main README.md
- [ ] Push changes
- [ ] Test Streamlit Cloud deployment

## Key Files to Reference

1. **HYBRID_REFACTORING_PLAN.md** - Detailed refactoring strategy
2. **FILE_MIGRATION_MAP.md** - Exact file movements to make
3. **CLAUDE.md** - General Claude instructions
4. **WHERE_TO_PUT_THINGS.md** - File organization guide (check if still valid)

## Important Notes

- **Pre-commit hook disabled**: Tests won't block commits during refactoring
- **Backup available**: Can revert to main-backup-20250114 if needed
- **Deployment branch**: Keep as reference, don't modify during refactoring
- **Known issues**: Document in DEPLOYMENT_ISSUES_YYYYMMDD.md format

## Commands for Common Tasks

```bash
# Re-enable pre-commit hook when done
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit

# Test deployment locally
streamlit run APE.py

# Check what Streamlit will deploy
# (After creating .streamlitignore)
find . -type f -name "*.py" | grep -v -f .streamlitignore

# Revert if needed
git checkout main-backup-20250114
```

## Decision Log

- **2025-01-14**: Decided on hybrid approach over separate repositories
- **2025-01-14**: Disabled pre-commit hooks for major refactoring
- **2025-01-14**: Created backup branch before starting

## Next Immediate Steps

1. Complete Phase 1 by adding README files to new directories
2. Start Phase 2 file movements following FILE_MIGRATION_MAP.md
3. Test application still runs after each major move

---
Remember: The goal is a clean, deployable main branch with organized research areas.