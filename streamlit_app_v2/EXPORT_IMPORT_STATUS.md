# Export/Import Feature Status

## Current State (2025-01-07)

### What's Implemented
1. **UI Structure** ✅
   - Simulations page with Recent Simulations list
   - Manage button with Export/Import tabs
   - Components properly organized in `components/` directory

2. **Core Functionality** ✅
   - `SimulationPackageManager` with security features
   - Package creation and validation logic
   - Comprehensive test suite

### What's Broken 🔴

#### 1. Export Functionality - Multiple Issues

##### 1a. Path Resolution Issue ✅ FIXED
**Error**: `Failed to create package: No metadata found at sim_20250607_104103_d590510c/metadata.json`
**Fix Applied**: Added proper path construction in export.py

##### 1b. ~~Stale Session State Issue~~ Actually: Small Simulations Not Saved to Disk! 🔴 ROOT CAUSE FOUND
**Error**: `Failed to create package: No metadata found at simulation_results/sim_20250607_112927_cc0efabf/metadata.json`

**Real Root Cause**: 
- Small simulations use `InMemoryResults` (< 10,000 patient-years)
- These are NEVER saved to disk in the current implementation
- Only `ParquetResults` (large simulations) are automatically saved
- The sim_id exists in session state but no directory was ever created

**Code Flow**:
1. `pages/2_Simulations.py` runs simulation
2. `ResultsFactory.create_results()` returns `InMemoryResults` for small sims
3. Results stored in session state BUT NOT SAVED TO DISK
4. Export tries to load from disk - directory doesn't exist!

**Fix Needed**:
```python
# In pages/2_Simulations.py after line 331:
# Save in-memory results to disk
if isinstance(results, InMemoryResults):
    save_path = ResultsFactory.DEFAULT_RESULTS_DIR / results.metadata.sim_id
    results.save(save_path)
```

#### 2. Import Functionality - Not Tested
Cannot test until export is working.

## Desired State

### 1. Working Export Flow
1. User selects simulation from Recent Simulations list
2. User clicks Manage → Export tab
3. User clicks "Download Package" button
4. Progress bar shows export stages
5. Download button appears with package ready
6. User downloads .zip file containing all simulation data

### 2. Working Import Flow  
1. User clicks Manage → Import tab
2. User uploads a .zip package file
3. System validates the package
4. System imports the simulation
5. Simulation appears in Recent Simulations with "IMPORTED" badge
6. User can analyze imported simulation

### 3. Package Contents
Each exported package should contain:
```
APE_simulation_[sim_id]_[date].zip
├── manifest.json         # Package metadata and checksums
├── data/
│   ├── patients.parquet  # Patient data
│   ├── visits.parquet    # Visit records
│   ├── metadata.parquet  # Simulation metadata
│   └── patient_index.parquet # Patient indexing
├── protocol.yaml         # Protocol specification
├── parameters.json       # Simulation parameters
├── audit_log.json       # Audit trail
└── README.txt           # Human-readable description
```

## Fix Plan

### Phase 1: Fix Export Path Issue
1. Update `components/export.py` to construct proper path
2. Add fallback handling for missing metadata
3. Test with existing simulations

### Phase 2: Verify Package Creation
1. Ensure all required files are included
2. Verify checksums are calculated correctly
3. Test package compression

### Phase 3: Test Import Flow
1. Export a test package
2. Import the package
3. Verify data integrity
4. Check "IMPORTED" badge display

### Phase 4: Error Handling
1. Add better error messages
2. Handle edge cases (missing files, corrupted data)
3. Add recovery suggestions

## Technical Details

### Path Resolution
The application uses a standard directory structure:
```
simulation_results/
├── sim_20250607_104103_d590510c/
│   ├── metadata.json
│   ├── summary_stats.json
│   ├── patients.parquet (if large simulation)
│   ├── visits.parquet (if large simulation)
│   └── results.pkl (if small simulation)
```

### Session State Keys
- `current_sim_id`: Currently selected simulation ID
- `imported_simulations`: Set of imported simulation IDs (for badges)
- `show_manage`: Toggle state for Manage section

## Testing Checklist

- [ ] Fix path resolution in export component
- [ ] Successfully export a simulation package
- [ ] Download and inspect package contents
- [ ] Import the package
- [ ] Verify imported simulation displays correctly
- [ ] Check all data is preserved
- [ ] Test with both small (in-memory) and large (parquet) simulations
- [ ] Test error cases (missing files, invalid packages)