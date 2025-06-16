# File Migration Map for Hybrid Refactoring

## Files to Move to archive/old_docs/

### Old Summaries and Reports
- ANATOMICAL_MODELING_RATIONALE.md
- APE_COMPONENTS_ANALYSIS.md
- CLINICAL_DISCONTINUATION_INSIGHTS.md
- COVID_GAP_ANALYSIS_SUMMARY.md
- DATA_FLOW_FIX_PLAN.md
- DES_INTEGRATION_TEST_FIXES.md
- DISCONTINUATION_FIX_SUMMARY.md
- DISCONTINUATION_TYPES_SUMMARY.md
- ENUM_CONSISTENCY_FIX.md
- ENUM_SERIALIZATION_MIGRATION.md
- FINANCIAL_SYSTEM_V2_MODERNIZATION_REPORT.md
- FINANCIAL_V2_IMPLEMENTATION_PLAN.md
- NEXT_STEPS_VA_FIX.md
- PANDAS_FREQUENCY_UPDATE.md
- PARQUET_MIGRATION_*.md
- PATIENT_STATE_FLAGS_IMPLEMENTATION.md
- PHASE*_SUMMARY.md
- PRICING_UPDATE_VALIDATION.md
- REFACTORING_*.md
- RETREATMENT_FIX_SUMMARY.md
- SESSION_SUMMARY_*.md
- STAGGERED_*.md
- STREAMGRAPH_*.md
- V2_*.md
- VA_FIX_IMPLEMENTATION.md
- VISIT_ENHANCEMENT_OPTIONS_ANALYSIS.md
- VISUALIZATION_FIX_GUIDE.md

## Files to Move to research/data_analysis/

### Data Directories
- aflibercept_2mg_data/
- eylea_high_dose_data/
- vegf_literature_data/

### Analysis Scripts
- analysis/*.py (all Python files)
- literature_extraction_results.json
- literature_parameter_summary.json

## Files to Move to research/experiments/

### From dev/experiments/
- All contents of dev/experiments/

### From scratchpad/
- All contents (visualization experiments)

### Root Level Experiments
- APE_DEBUG.py
- APE_NO_CARBON.py
- COMPARE_SETUP.py
- TEST_*.py (test scripts, not unit tests)

## Files to Move to research/test_scripts/

### From dev/test_scripts/
- All contents (debug and validation scripts)

### Simulation Test Scripts
- run_ape.py.bak
- hello.py
- test_data_structure.json
- test_enrollment.csv
- test_enrollment_viz.R
- test_minimal_config.yaml
- test_r_viz.sh

## Files to Move to tests/

### Existing test directories
- tests/* (keep current structure)
- tests_v2/* (if exists)

### Scattered test files
- test_*.py from root
- conftest.py
- pytest.ini

## Files to Keep in docs/

### Deployment Documentation
- DEPLOYMENT_CHECKLIST.md
- DEPLOYMENT_GUIDE.md
- CLOUD_DEPLOYMENT_GUIDE.md
- README_*.md

### Development Documentation
- WHERE_TO_PUT_THINGS.md
- REQUIREMENTS_README.md
- MCP_SERVERS_README.md

### Keep CLAUDE files in root
- CLAUDE.md
- CLAUDE.local.md
- CLAUDE_APP_SPECIFIC.md

## Files to Keep in Root (Deployment)

### Core Application
- APE.py
- pages/
- ape/
- protocols/
- visualization/
- assets/

### Configuration
- requirements.txt
- requirements-dev.txt
- runtime.txt
- Dockerfile
- .streamlit/
- .gitignore
- .gitmodules
- .python-version

### Documentation
- README.md
- LUKE.md (user notes)

## Files to Delete/Ignore

### Temporary/Generated
- *.log
- *.pyc
- __pycache__/
- .pytest_cache/
- node_modules/
- venv/
- simulation_results/
- output/
- debug_output/

### Old Backups
- *.bak
- *.conflict

## Special Cases

### Paper Directory
- Keep Paper/ as is (already well-organized)

### Meta Directory  
- Keep meta/ but review contents:
  - Move old plans to archive/old_docs/
  - Keep current design docs and postmortems

### Scripts Directory
- scripts/ - keep for deployment/development scripts

### Migration Directory
- migration/ - move to archive/ after refactoring complete

## Directory Creation Script

```bash
#!/bin/bash
# Create hybrid structure

# Main directories
mkdir -p archive/{legacy_apps,old_docs}
mkdir -p research/{data_analysis,experiments,test_scripts}
mkdir -p tests/{unit,integration,regression}
mkdir -p docs/{deployment,development,api}

# Create README files
echo "# Archive Directory
Historical code and documentation preserved for reference." > archive/README.md

echo "# Research Directory  
Active development and analysis work not part of deployment." > research/README.md

echo "# Tests Directory
All project tests organized by type." > tests/README.md
```

## Verification Checklist

After migration:
- [ ] `ls -la` shows clean root with <20 files
- [ ] All .md summaries moved to archive/old_docs/
- [ ] All data analysis in research/data_analysis/
- [ ] All experiments in research/experiments/
- [ ] All tests consolidated in tests/
- [ ] .streamlitignore created and tested
- [ ] App still runs with `streamlit run APE.py`