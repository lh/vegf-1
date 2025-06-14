# Active Instructions - Hybrid Repository Refactoring

**IMPORTANT**: This is the primary instruction file. Always check this file at the start of each session.

## 🚨 Current Active Task: Hybrid Repository Refactoring
**Status**: Phase 1 In Progress  
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

### ⏳ Phase 2: Move Files
Follow FILE_MIGRATION_MAP.md to move:
- [ ] Archive old summaries and reports
- [ ] Move research/analysis files
- [ ] Move experimental code
- [ ] Consolidate all tests
- [ ] Organize documentation

### ⏳ Phase 3: Create .streamlitignore
- [ ] Create comprehensive .streamlitignore file
- [ ] Test deployment exclusions work

### ⏳ Phase 4: Clean Root Directory
- [ ] Ensure root has only essential files
- [ ] Update any broken imports
- [ ] Test application still runs

### ⏳ Phase 5: Merge Deployment Improvements
- [ ] Bring in Altair fixes from deployment branch
- [ ] Bring in other improvements
- [ ] Document known issues (entry point, Altair aesthetics)

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