# Simulation Package Export/Import Proposal

## Executive Summary
Add functionality to export simulation results as portable packages and import them for analysis, enabling collaboration and reproducibility.

## Problem Statement
Currently, simulation results only exist within a user's session. Users cannot:
- Share simulation results with colleagues
- Archive simulations for regulatory compliance
- Compare results across different runs or users
- Reproduce exact analyses from previous work

## Proposed Solution
Implement a bidirectional simulation package format that preserves all data and metadata needed to perfectly reproduce an analysis.

## Package Structure
```
APE_simulation_[sim_id]_[YYYYMMDD].zip
├── manifest.json          # Package metadata and version info
├── data/
│   ├── patients.parquet   # Patient-level data
│   ├── visits.parquet     # Visit records
│   └── metadata.parquet   # Simulation metadata
├── protocol.yaml          # Exact protocol specification
├── parameters.json        # Simulation parameters
├── summary_stats.json     # Pre-calculated statistics
├── audit_log.json         # Complete audit trail
└── README.txt            # Human-readable description
```

## Implementation Plan

### Phase 1: Export Functionality
1. **Add to Audit Trail tab** in Analysis Overview
   - "Download Simulation Package" button
   - Show package size estimate
   - Include download timestamp

2. **Package Generation**
   ```python
   def create_simulation_package(results, protocol, params, audit_log):
       # Create temp directory
       # Copy/convert data files (memory → parquet if needed)
       # Generate manifest with checksums
       # Create README with summary
       # Zip everything
       # Return bytes for download
   ```

3. **Smart Format Selection**
   - Internal format: Always parquet for data integrity
   - Optional: Include `results_preview.csv` for small datasets (<10MB)
   - README explains how to open parquet files

### Phase 2: Import Functionality
1. **Add to Protocol Manager page**
   - "Import Simulation" button (in Manage dropdown?)
   - File upload for .zip packages
   - Validation and preview before import

2. **Import Process**
   ```python
   def import_simulation_package(uploaded_file):
       # Validate zip structure
       # Check manifest version compatibility
       # Extract to temp location
       # Load data into SimulationResults object
       # Populate session state
       # Redirect to Analysis Overview
   ```

3. **UI Indicators**
   - Banner: "Viewing imported simulation from [date]"
   - Audit trail shows import providence
   - Disable "Run Simulation" for imported results

## Technical Considerations

### Data Integrity
- Include checksums in manifest
- Validate data consistency on import
- Preserve data types exactly (parquet handles this well)

### Version Management
```json
{
  "package_version": "1.0",
  "ape_version": "2.0.0",
  "created_date": "2025-06-03T10:30:00Z",
  "created_by": "user@example.com"
}
```

### Storage Optimization
- Compress parquet files within zip
- Exclude redundant data
- Estimate: ~10-20% of original data size

### Security Considerations
- Validate file sizes before extraction
- Sanitize file paths
- Check for malicious content in YAML/JSON
- Optional: Sign packages for authenticity

## User Benefits
1. **Collaboration**: Share exact results with team members
2. **Reproducibility**: Perfect recreation of previous analyses  
3. **Archival**: Long-term storage for compliance
4. **Comparison**: Load multiple simulations for comparison
5. **Debugging**: Share problematic simulations for support

## Success Metrics
- Successful round-trip: Export → Import → Identical Analysis
- Package size < 20% of memory footprint
- Import time < 5 seconds for typical simulations
- Zero data loss in round-trip

## Future Enhancements
1. **Batch Operations**: Export/import multiple simulations
2. **Cloud Storage**: Direct upload to S3/GCS
3. **Differential Packages**: Only changes from baseline
4. **Package Viewer**: Standalone tool to inspect packages

## Timeline Estimate
- Phase 1 (Export): 2-3 days
- Phase 2 (Import): 2-3 days  
- Testing & Documentation: 2 days
- Total: ~1 week

## Questions to Resolve
1. Should we encrypt sensitive data?
2. Maximum package size limits?
3. Retention policy for imported simulations?
4. Support for partial imports (just protocol, just results)?

---
*Proposed by: Claude  
Date: 2025-06-03  
Status: Draft*