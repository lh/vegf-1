# Streamlit to Parquet Migration Plan

**Created:** 2025-05-23
**Purpose:** Migrate Streamlit app from JSON-based to Parquet-based data pipeline
**Status:** Planning Phase

## Executive Summary

We're migrating from a dual-pipeline system (JSON for Streamlit, Parquet for standalone visualizations) to a unified Parquet-based architecture. This will provide richer data (including proper discontinuation types and retreatment tracking) to all visualizations.

## Problem Statement

- **Current State**: Two incompatible data pipelines
  - JSON pipeline: Simple phase information, no discontinuation flags
  - Parquet pipeline: Rich data with full state tracking and categorization
- **Issue**: Trying to bridge between formats loses data fidelity
- **Solution**: Standardize on the proven Parquet pipeline

## Migration Strategy

### Core Principle: Clone and Migrate
- Keep existing `streamlit_app/` untouched
- Create `streamlit_app_parquet/` as migration target
- Use "Strangler Fig" pattern for gradual replacement

## Detailed Implementation Plan

### Phase 1: Foundation (Days 1-2)
1. **Clone Application**
   ```bash
   cp -r streamlit_app/ streamlit_app_parquet/
   ```

2. **Create Feature Flag System**
   - Add `USE_PARQUET_PIPELINE` environment variable
   - Implement pipeline switching in `app.py`
   - Default to existing JSON pipeline initially

3. **Set Up Testing Infrastructure**
   - Create `tests/parquet_migration/` directory
   - Write comparison tests for data outputs
   - Set up parallel run capability

### Phase 2: Core Data Pipeline (Days 3-5)
1. **Analyze Existing Parquet Pipeline**
   - Study `run_streamgraph_simulation_parquet.py`
   - Document data enrichment logic
   - Identify all state flag generation

2. **Modify simulation_runner.py**
   - Import Parquet generation logic
   - Replace JSON serialization with Parquet writing
   - Ensure all enrichment flags are included

3. **Update Data Loading**
   - Create `parquet_data_loader.py`
   - Replace JSON reading with Parquet reading
   - Maintain same interface for visualizations

### Phase 3: Visualization Migration (Days 6-10)
1. **Start with Streamgraph** (Already Parquet-compatible!)
   - Integrate existing `create_current_state_streamgraph.py`
   - Integrate existing `create_patient_state_streamgraph.py`
   - Remove bridge function complexity

2. **Create Adapter Layer**
   ```python
   class ParquetDataAdapter:
       """Provides compatible interface for existing visualizations"""
       def get_patient_histories(self):
           # Convert Parquet to expected format
       def get_summary_stats(self):
           # Extract from Parquet metadata
   ```

3. **Migrate Other Visualizations**
   - Visual acuity plots
   - Discontinuation charts
   - Treatment timeline
   - Test each thoroughly

### Phase 4: Validation (Days 11-12)
1. **Parallel Testing**
   - Run same simulation through both pipelines
   - Compare all outputs
   - Document any discrepancies

2. **Performance Testing**
   - Measure load times
   - Check memory usage
   - Optimize where needed

3. **Data Integrity Checks**
   - Verify patient counts preserved
   - Check state transitions valid
   - Ensure no data loss

### Phase 5: Cutover (Days 13-14)
1. **Gradual Rollout**
   - Enable for development first
   - Test with subset of users
   - Monitor for issues

2. **Full Migration**
   - Switch feature flag to Parquet default
   - Keep JSON pipeline available for rollback
   - Document new data flow

3. **Cleanup** (Week 3+)
   - Remove JSON pipeline code
   - Delete bridge functions
   - Update all documentation

## Technical Details

### Key Files to Modify
1. `streamlit_app_parquet/simulation_runner.py`
   - Main integration point for Parquet generation

2. `streamlit_app_parquet/models/simulation_results.py`
   - Update to work with Parquet DataFrames

3. `streamlit_app_parquet/pages/run_simulation.py`
   - Remove bridge function, use Parquet directly

### Data Schema Alignment
```python
# Parquet schema includes:
visits_df = pd.DataFrame({
    'patient_id': str,
    'date': datetime,
    'phase': str,
    'discontinuation_type': str,  # Rich categorization
    'is_retreatment_visit': bool,
    'cumulative_injections': int,
    # ... more enriched fields
})
```

### Benefits Realized
1. **Immediate**: Streamgraph shows all discontinuation types
2. **Short-term**: All visualizations get richer data
3. **Long-term**: Single pipeline to maintain

## Success Criteria

1. All visualizations produce equivalent or better output
2. No data loss during migration
3. Performance equal or better than JSON pipeline
4. All tests passing
5. Documentation updated

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|---------|------------|
| Breaking existing functionality | High | Keep both pipelines, extensive testing |
| Data format incompatibilities | Medium | Adapter layer, gradual migration |
| Performance regression | Low | Benchmark before/after, optimize |
| Missing edge cases | Medium | Comprehensive test suite |

## Next Steps for Fresh Session

When starting the implementation:

1. **First Actions**:
   ```bash
   # 1. Create the clone
   cp -r streamlit_app/ streamlit_app_parquet/
   
   # 2. Create feature flag
   echo "USE_PARQUET_PIPELINE=false" >> .env
   
   # 3. Start modifying simulation_runner.py
   ```

2. **Key Focus Areas**:
   - Study how `run_streamgraph_simulation_parquet.py` enriches data
   - Preserve that enrichment logic exactly
   - Test with small datasets first

3. **Validation Approach**:
   - Always compare JSON vs Parquet outputs
   - Use existing streamgraph images as reference
   - Ensure discontinuation types match exactly

## Reference Materials

- `run_streamgraph_simulation_parquet.py` - The golden source for enrichment logic
- `meta/patient_state_visualization_definitions_20250522.md` - State mappings
- Existing streamgraph images - Proof that Parquet pipeline works correctly

---

**Remember**: The Parquet pipeline already works perfectly for streamgraphs. We're not inventing anything new, just unifying what already exists.