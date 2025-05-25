# Streamlit Streamgraph Integration Roadmap

**Created:** 2025-05-22 20:15:00  
**Context:** Integrating patient state streamgraph visualizations into Streamlit application

## Current Status

### ✅ Completed
1. **Fixed Streamlit working directory issue** - Added working directory check in app.py
2. **Removed redundant visualization code** - Cleaned up old discontinuation charts
3. **Created new streamgraph visualizations**:
   - `create_patient_state_streamgraph.py` (cumulative view)
   - `create_current_state_streamgraph.py` (current state view)
4. **Added UI framework** - Tabs and expandable glossary in run_simulation.py
5. **Defined clinical labels** - Clear state definitions with British English spelling

### ✅ Recently Completed (23rd May 2025)
- **Bridge function development** - Created `streamlit_app/streamgraph_bridge.py`
- **Current state view integration** - Successfully integrated and working

### 🚧 In Progress
- **Cumulative view integration** - Next visualization to integrate

### 📋 Immediate Next Steps
1. ~~**Create bridge function**~~ ✓ DONE - `convert_streamlit_to_streamgraph_format()`
2. ~~**Complete current state view integration**~~ ✓ DONE
3. **Add cumulative view integration** - Next task
4. **Test and refine clinical tooltips**

## Data Flow Analysis

### Current Architecture
```
Simulation → patient_histories → Two different paths:

Path A (Streamlit): 
TreatAndExtendABS.run() → simulation_runner.py → results dict → Streamlit UI

Path B (Standalone):
TreatAndExtendABS.run() → run_streamgraph_simulation_parquet.py → Parquet files → streamgraph scripts
```

### Key Finding
Both paths have the same underlying `patient_histories` data from `sim.run()`, just packaged differently:
- **Streamlit**: `results["patient_histories"]` (dict format)
- **Standalone**: Parquet files with explicit state flags

## Future Refactoring Opportunity

### Vision: Unified Parquet-Based Architecture

**Proposed Future State:**
```
Simulation → Parquet files → All visualizations use consistent format

TreatAndExtendABS.run() → enhanced_simulation_runner.py → Parquet files → {
  - Streamlit UI
  - Standalone streamgraphs  
  - All other visualizations
}
```

### Benefits of Parquet Refactoring
1. **Consistent data format** across all visualization tools
2. **Better performance** with columnar storage
3. **Type safety** and data validation
4. **Easier debugging** with standard file format
5. **Simplified data pipeline** architecture

### Migration Requirements
- **Modify simulation_runner.py** to save Parquet files instead of dict processing
- **Update all existing visualizations** to read from Parquet format
- **Standardize state flag generation** across all simulation types
- **Create data schema validation** for Parquet outputs
- **Update Streamlit caching** to work with file-based data

### Effort Estimate
- **High complexity** - affects core data pipeline
- **Multiple components** need coordinated changes
- **Backward compatibility** considerations for existing workflows
- **Testing overhead** to ensure no regression

## Implementation Strategy

### Phase 1: Bridge Solution (Current)
- Create conversion functions for immediate integration
- Maintain existing architecture
- Get streamgraph visualizations working in Streamlit

### Phase 2: Parquet Migration (Future)
- Plan comprehensive refactoring
- Design unified data schema
- Implement incremental migration
- Validate all visualization components

## Technical Notes

### Current Data Conversion Challenge
The Streamlit `results` dict contains:
- `results["patient_histories"]` - raw simulation data
- Various processed metrics and statistics
- UI-specific formatting and metadata

Our streamgraph functions expect:
- Pandas DataFrames with explicit state flags
- Standardized column names and types
- Temporal data in specific formats

### Bridge Function Requirements ✓ IMPLEMENTED
1. **Extract patient_histories** from Streamlit results ✓
2. **Apply state flag logic** (currently in run_streamgraph_simulation_parquet.py) ✓
3. **Convert to DataFrame format** expected by streamgraph functions ✓
4. **Handle metadata conversion** for proper visualization ✓

### Implementation Details (23rd May 2025)

**Key Files Created/Modified:**
- `streamlit_app/streamgraph_bridge.py` - Main bridge module with conversion functions
- `streamlit_app/pages/run_simulation.py` - Updated to use bridge function
- Metadata format aligned with streamgraph expectations:
  - `n_patients` → `patients`
  - Added `duration_years` calculation
  - Added `simulation_type` field

**Key Functions:**
- `convert_streamlit_to_streamgraph_format()` - Main conversion function
- `_create_visits_dataframe()` - Converts patient histories to visits DataFrame
- `_create_metadata_dataframe()` - Creates metadata in expected format
- `_create_stats_dataframe()` - Generates statistics DataFrame
- `_map_discontinuation_type()` - Maps reasons to standardized types

---

**Priority:** Medium-High (after current integration complete)  
**Dependencies:** Successful bridge function implementation  
**Risk:** Medium (affects multiple components)  
**Timeline:** Future iteration (not current sprint)