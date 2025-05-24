# Parquet Migration - Day 2 Plan

**Date**: 2025-05-24
**Goal**: Migrate remaining visualizations to use Parquet DataFrames

## What We Have So Far

✅ **Completed (Day 1)**:
- Clean Parquet-only Streamlit app in `streamlit_app_parquet/`
- Patient State Visualizations (Current & Cumulative views)
- Enriched data with all discontinuation types
- Clinical color scheme

## Today's Tasks

### 1. Identify Remaining Visualizations
Need to migrate:
- Visual Acuity plots (mean over time, distribution)
- Discontinuation charts
- Treatment timeline
- Retreatment panel
- Any other charts using patient data

### 2. Create Data Adapter
Since other visualizations expect the old format, we need:
- A clean adapter to convert Parquet DataFrames to expected format
- Ensure no data loss in conversion
- Maintain performance

### 3. Update Each Visualization
For each chart:
- Identify what data it needs
- Update to use Parquet DataFrames
- Test thoroughly
- Ensure consistent styling with color system

### 4. Remove Old Data Structures
Once all visualizations work:
- Remove dependencies on old patient_histories dict format
- Clean up any conversion code
- Ensure everything uses DataFrames directly

## Priority Order

1. **Visual Acuity plots** - Core metric visualization
2. **Discontinuation breakdown** - Already have the data
3. **Retreatment panel** - Important for analysis
4. **Other charts** - As needed

## Success Criteria

- All visualizations show same or better information
- No loss of functionality
- Consistent use of Parquet DataFrames
- Clean, maintainable code

Let's get started! 🚀