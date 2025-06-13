# Root Directory Cleanup Plan

## Current Situation
The root directory has ~400+ files that should be organized!

## File Categories and Proposed Locations

### 1. 🧪 Test/Debug Scripts (~200+ files)
**Pattern**: `test_*.py`, `debug_*.py`, `verify_*.py`, `fix_*.py`, `validate_*.py`
**Examples**: 
- test_streamgraph.py
- debug_discontinuation.py
- verify_fixed_discontinuation.py
- fix_streamgraph_visualization.py

**Proposed Location**: `dev/test_scripts/`

### 2. 📊 Generated Visualizations/Data (~100+ files)
**Pattern**: `*.png`, `*.csv`, `*.json` (output files)
**Examples**:
- abs_mean_acuity.png
- patient_data_check.json
- fixed_monthly_data.csv

**Proposed Location**: `output/` (gitignored)

### 3. 📝 Documentation/Planning (~50+ files)
**Pattern**: `*_SUMMARY.md`, `*_PLAN.md`, `*_GUIDE.md`
**Examples**:
- STREAMGRAPH_FIX_SUMMARY.md
- ECONOMIC_ANALYSIS_PLANNING.md
- PARQUET_MIGRATION_PLAN.md

**Proposed Location**: `meta/planning/`

### 4. 🔧 Utility/Analysis Scripts (~50+ files)
**Pattern**: `analyze_*.py`, `extract_*.py`, `compare_*.py`, `run_*.py`
**Examples**:
- analyze_visits.py
- extract_baseline_va.py
- compare_treatment_protocols.py

**Proposed Location**: `scripts/analysis/`

### 5. 🚀 Deployment/Setup Scripts
**Pattern**: `setup_*.sh`, `install_*.sh`, `start_*.sh`
**Examples**:
- setup_conda.sh
- install-mcp-servers.sh

**Proposed Location**: `scripts/setup/`

### 6. 📋 Protocol/Clinical Files
**Pattern**: `*_PROTOCOL_*.md`, clinical analysis files
**Examples**:
- AFLIBERCEPT_2MG_PROTOCOL_SUMMARY.md
- EYLEA_8MG_PROTOCOL_SUMMARY.md

**Proposed Location**: `literature_extraction/summaries/`

### 7. 🗑️ Temporary/Old Files
**Pattern**: `.bak`, `.old`, `_orig`, session files
**Examples**:
- run_ape.py.bak
- instructions.old.md

**Proposed Location**: DELETE or `archive/temp/`

### 8. ✅ Files That Should Stay at Root
- APE.py (main entry)
- README.md
- requirements.txt, requirements-dev.txt
- pytest.ini
- Dockerfile, .dockerignore
- .gitignore, .gitmodules
- .env (if needed)
- CLAUDE.md (project instructions)
- Package files (package.json, etc.)

## Proposed New Structure

```
vegf-1/
├── APE.py                    # Keep
├── README.md                 # Keep
├── requirements*.txt         # Keep
├── pytest.ini               # Keep
├── Dockerfile               # Keep
├── .dockerignore            # Keep
├── .gitignore               # Keep
├── CLAUDE.md                # Keep
│
├── dev/
│   ├── test_scripts/        # All test_*.py, debug_*.py, verify_*.py
│   ├── experiments/         # (existing)
│   ├── pages/              # (existing)
│   └── migration/          # (existing)
│
├── scripts/
│   ├── analysis/           # analyze_*.py, extract_*.py, compare_*.py
│   ├── simulation/         # run_*.py simulation scripts
│   └── setup/              # setup_*.sh, install_*.sh
│
├── meta/
│   ├── planning/           # All planning/summary markdown files
│   ├── clinical_summaries/ # Protocol summaries
│   └── refactoring_plans/  # (existing)
│
├── output/                 # All generated files (gitignored)
│   ├── plots/             # *.png files
│   ├── data/              # *.csv, *.json output
│   └── logs/              # *.log files
│
└── archive/
    └── temp/              # Old/backup files
```

## Implementation Strategy

### Phase 1: Create Directory Structure
```bash
mkdir -p dev/test_scripts
mkdir -p scripts/{analysis,simulation,setup}
mkdir -p meta/{planning,clinical_summaries}
mkdir -p output/{plots,data,logs}
mkdir -p archive/temp
```

### Phase 2: Move Files by Category
1. Move test/debug scripts to `dev/test_scripts/`
2. Move output files to `output/`
3. Move documentation to `meta/`
4. Move utility scripts to `scripts/`
5. Delete or archive old files

### Phase 3: Update .gitignore
Add to .gitignore:
```
# Output directory
output/
!output/.gitkeep

# Temporary files
archive/temp/
```

### Phase 4: Verify Nothing Breaks
- Check imports in remaining files
- Ensure APE.py still runs
- Update any hardcoded paths

## Benefits
1. **Clean root**: Only essential files at root
2. **Logical organization**: Easy to find files by type
3. **Better deployment**: Clear what to include/exclude
4. **Improved development**: Less clutter, better focus

## Questions to Consider
1. Should we keep ANY test scripts at root?
2. Are there specific output files that should be preserved?
3. Should clinical summaries go in literature_extraction instead?
4. Any files that are actively used and need special handling?