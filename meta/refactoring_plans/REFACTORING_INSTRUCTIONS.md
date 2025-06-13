# Refactoring Instructions

This document provides step-by-step instructions for refactoring the VEGF-1 repository to separate the three distinct systems.

## Prerequisites

1. Ensure all work is committed and pushed
2. Verify tests are passing: `python streamlit_app_v2/scripts/run_tests.py`
3. Have GitHub CLI installed for creating new repositories

## Phase 1: Setup and Preparation

### 1.1 Create Feature Branch
```bash
# Ensure we're on main and up to date
git checkout main
git pull

# Create and checkout feature branch
git checkout -b feature/three-system-refactor

# Tag current state for rollback if needed
git tag pre-refactor-backup-v2
```

### 1.2 Create Directory Structure
```bash
# Create new directories
mkdir -p literature_extraction/scripts
mkdir -p development/{experiments,debug_pages,test_scripts}
mkdir -p clinical_analysis/{analysis,scripts}
mkdir -p archive

# Create README files
touch literature_extraction/README.md
touch development/README.md
touch clinical_analysis/MIGRATION_NOTES.md
```

### 1.3 Create Directory Documentation
```bash
# Create literature_extraction/README.md
cat > literature_extraction/README.md << 'EOF'
# Literature Extraction Tools

This directory contains tools for extracting parameters from academic literature.

## Contents
- `aflibercept_2mg_data/` - Aflibercept 2mg study data (submodule)
- `eylea_high_dose_data/` - High-dose Eylea data (submodule)
- `vegf_literature_data/` - VEGF literature collection (submodule)
- `scripts/` - Extraction and analysis scripts

## Note
These tools are for development/research only and are excluded from production deployment.
EOF

# Create development/README.md
cat > development/README.md << 'EOF'
# Development Tools

This directory contains development-only tools and experiments.

## Contents
- `experiments/` - Experimental features and prototypes
- `debug_pages/` - Debug Streamlit pages (98_, 99_)
- `test_scripts/` - Testing utilities and scripts

## Note
Everything in this directory is excluded from production deployment.
EOF

# Create clinical_analysis/MIGRATION_NOTES.md
cat > clinical_analysis/MIGRATION_NOTES.md << 'EOF'
# Clinical Analysis Migration Notes

This directory contains real-world clinical data analysis tools that will be moved to a separate repository.

## Migration Plan
1. Create new repository: `vegf-clinical-analysis`
2. Move this entire directory to the new repository
3. Update imports and dependencies
4. Set up appropriate access controls

## Security Considerations
- These tools work with real patient data
- Requires strict access controls
- Should be deployed on-premises
- May require HIPAA compliance
EOF
```

## Phase 2: Extract Core APE Application

### 2.1 Move APE.py to Root
```bash
git mv streamlit_app_v2/APE.py ./
```

### 2.2 Move Core Directories
```bash
# Move all core application directories
git mv streamlit_app_v2/pages ./
git mv streamlit_app_v2/components ./
git mv streamlit_app_v2/core ./
git mv streamlit_app_v2/utils ./
git mv streamlit_app_v2/visualizations ./
git mv streamlit_app_v2/protocols ./
git mv streamlit_app_v2/assets ./
git mv streamlit_app_v2/.streamlit ./
git mv streamlit_app_v2/simulation_results ./

# Move test infrastructure
git mv streamlit_app_v2/tests ./
git mv streamlit_app_v2/scripts ./
```

### 2.3 Handle Requirements
```bash
# If streamlit_app_v2 has its own requirements
if [ -f streamlit_app_v2/requirements.txt ]; then
    cp streamlit_app_v2/requirements.txt requirements-app.txt
    echo "# Review requirements-app.txt and merge with main requirements.txt"
fi
```

### 2.4 Update CLAUDE.md
```bash
# Append v2-specific instructions to main CLAUDE.md
if [ -f streamlit_app_v2/CLAUDE.md ]; then
    echo -e "\n\n# === Instructions from streamlit_app_v2 ===\n" >> CLAUDE.md
    cat streamlit_app_v2/CLAUDE.md >> CLAUDE.md
fi
```

## Phase 3: Organize Literature Extraction

### 3.1 Move Extraction Scripts
```bash
# Move root-level extraction scripts
git mv extract_*.py literature_extraction/scripts/
git mv protocol_parameters.py literature_extraction/scripts/

# Move parameter estimation
git mv analysis/parameter_estimation.py literature_extraction/scripts/
```

### 3.2 Verify Submodules
```bash
# Submodules should already be at root - just document them
echo "Submodules for literature extraction:" > literature_extraction/SUBMODULES.txt
echo "- aflibercept_2mg_data/" >> literature_extraction/SUBMODULES.txt
echo "- eylea_high_dose_data/" >> literature_extraction/SUBMODULES.txt  
echo "- vegf_literature_data/" >> literature_extraction/SUBMODULES.txt
```

## Phase 4: Organize Development Tools

### 4.1 Move Experiments
```bash
# Move experiments directory
if [ -d streamlit_app_v2/experiments ]; then
    git mv streamlit_app_v2/experiments/* development/experiments/
fi
```

### 4.2 Move Debug Pages
```bash
# Move debug pages
git mv streamlit_app_v2/pages/98_*.py development/debug_pages/ 2>/dev/null || true
git mv streamlit_app_v2/pages/99_*.py development/debug_pages/ 2>/dev/null || true
```

## Phase 5: Separate Clinical Analysis

### 5.1 Move Analysis Directory
```bash
# Move the entire analysis directory
git mv analysis/* clinical_analysis/analysis/
```

### 5.2 Move Analysis Scripts
```bash
# Move root-level analysis scripts
git mv analyze_*.py clinical_analysis/scripts/

# Move real data inspection tools
git mv test_real_data_streamgraph.py clinical_analysis/scripts/
git mv streamlit_app_parquet/inspect_real_data.py clinical_analysis/scripts/inspect_real_data_parquet.py
git mv streamlit_app/inspect_real_data.py clinical_analysis/scripts/inspect_real_data_legacy.py
```

### 5.3 Create Migration Script
```bash
cat > clinical_analysis/prepare_migration.sh << 'EOF'
#!/bin/bash
# Script to prepare clinical analysis tools for migration to separate repository

echo "Preparing clinical analysis tools for migration..."

# Create list of dependencies
echo "Extracting dependencies..."
grep -h "^import\|^from" scripts/*.py analysis/*.py | \
    grep -v "^\s*#" | \
    sort -u > DEPENDENCIES.txt

echo "Clinical analysis tools ready for migration."
echo "Next steps:"
echo "1. Create new repository: gh repo create vegf-clinical-analysis --private"
echo "2. Copy this directory to the new repository"
echo "3. Set up requirements.txt based on DEPENDENCIES.txt"
echo "4. Update imports to remove dependencies on main repository"
EOF

chmod +x clinical_analysis/prepare_migration.sh
```

## Phase 6: Archive Historical Code

### 6.1 Move Old Applications
```bash
# Archive old applications
git mv streamlit_app archive/
git mv streamlit_app_parquet archive/
git mv simulation archive/

# Archive now-empty v2 directory
git mv streamlit_app_v2 archive/
```

### 6.2 Create Archive Documentation
```bash
cat > archive/README.md << 'EOF'
# Historical Code Archive

This directory contains historical implementations preserved for reference.

## Contents

### streamlit_app/
- Original Streamlit application
- First iteration of the APE platform

### streamlit_app_parquet/
- Experimental Parquet-based implementation
- Contains 17+ streamgraph visualization experiments
- Valuable for understanding data pipeline evolution

### simulation/
- Original simulation engine (replaced by simulation_v2)
- Contains early agent-based simulation attempts

### streamlit_app_v2/
- Empty directory structure after extraction to root
- Kept to preserve git history

## Usage
These archives are for historical reference only. The active application is at the root level.
EOF
```

## Phase 7: Testing and Validation

### 7.1 Test Core APE Application
```bash
# Test that APE runs from root
streamlit run APE.py

# Run test suite
python scripts/run_tests.py --all

# Run validation scripts
python validation/verify_fixed_discontinuation.py
python validation/verify_streamlit_integration.py
```

### 7.2 Test Literature Extraction
```bash
# Test one extraction script
cd literature_extraction/scripts
python extract_baseline_va.py --test
cd ../..
```

### 7.3 Test Clinical Analysis
```bash
# Verify clinical analysis tools are properly organized
ls -la clinical_analysis/analysis/
ls -la clinical_analysis/scripts/
```

## Phase 8: Create Deployment Branch

### 8.1 Create .gitignore for Deployment
```bash
cat > .gitignore.deployment << 'EOF'
# Deployment exclusions
/archive/
/clinical_analysis/
/literature_extraction/
/development/
/notebooks/
**/debug_*.py
**/test_*.py
**/*_test.py
**/experiments/
**/__pycache__/
*.pyc
EOF
```

### 8.2 Commit All Changes
```bash
# Add all changes
git add -A

# Commit with detailed message
git commit -m "refactor: Separate three distinct systems

- Extracted core APE application to root
- Organized literature extraction tools
- Prepared clinical analysis for separate repository
- Archived historical implementations

Core APE application now ready for deployment.
Clinical analysis tools ready for migration.
Literature extraction organized but retained."
```

### 8.3 Create Deployment Branch
```bash
# Create deployment branch
git checkout -b deployment

# Remove non-deployment directories
rm -rf archive/
rm -rf clinical_analysis/
rm -rf literature_extraction/
rm -rf development/
rm -rf notebooks/

# Update .gitignore
cp .gitignore.deployment .gitignore

# Commit deployment state
git add -A
git commit -m "deployment: Remove non-production code

This branch contains only the core APE simulation platform.
Ready for production deployment."
```

## Phase 9: Create Clinical Analysis Repository

### 9.1 Prepare Migration
```bash
# Switch back to feature branch
git checkout feature/three-system-refactor

# Run preparation script
cd clinical_analysis
./prepare_migration.sh
cd ..
```

### 9.2 Create New Repository
```bash
# Create private repository for clinical analysis
gh repo create vegf-clinical-analysis --private --description "Clinical data analysis tools for VEGF studies"

# Clone new repository
cd ..
git clone https://github.com/[username]/vegf-clinical-analysis.git

# Copy clinical analysis tools
cp -r CC-finance/clinical_analysis/* vegf-clinical-analysis/

# Set up new repository
cd vegf-clinical-analysis
git add -A
git commit -m "Initial commit: Clinical analysis tools from vegf-1"
git push
```

## Phase 10: Final Steps

### 10.1 Update Main Repository
```bash
# Return to main repository
cd ../CC-finance

# Update README with new structure
# Document the three-system separation
# Add links to clinical analysis repository (if appropriate)
```

### 10.2 Create Pull Request
```bash
# Push feature branch
git push -u origin feature/three-system-refactor

# Create PR
gh pr create --title "Refactor: Separate three distinct systems" \
  --body "This PR refactors the repository to separate:
  
1. Core APE simulation platform (deployment ready)
2. Clinical analysis tools (prepared for separate repository)
3. Literature extraction tools (organized but retained)

The deployment branch contains only production code."
```

## Verification Checklist

- [ ] APE.py runs from root directory
- [ ] All tests pass
- [ ] Literature extraction tools are organized
- [ ] Clinical analysis tools are ready for migration
- [ ] Historical code is archived
- [ ] Deployment branch contains only core APE
- [ ] Documentation is updated
- [ ] No broken imports
- [ ] Submodules still function

## Rollback Plan

If issues arise:
```bash
# Return to pre-refactor state
git checkout main
git reset --hard pre-refactor-backup-v2

# Delete problematic branches
git branch -D feature/three-system-refactor
git branch -D deployment
```

## Notes

- The clinical analysis repository should have restricted access
- Consider setting up CI/CD for the deployment branch only
- Literature extraction tools can be updated independently
- The archive directory can be removed after 3-6 months if not needed