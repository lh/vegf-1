# Parquet Migration - Session Start Instructions

**Context**: We discovered that the Streamlit app uses a JSON pipeline missing discontinuation data, while the Parquet pipeline has all the rich data we need. We're migrating to use Parquet everywhere.

## What You're Building

Converting the Streamlit app from JSON-based to Parquet-based data pipeline to get rich discontinuation categorization and retreatment tracking in all visualizations.

## Key Background

1. **Two Pipelines Exist**:
   - JSON: `simulation_runner.py` → basic phase data only
   - Parquet: `run_streamgraph_simulation_parquet.py` → full enriched data with discontinuation types

2. **Proof It Works**: 
   - Check the existing streamgraph images in the previous conversation
   - They show proper categorization: Planned, Administrative, Duration, etc.
   - This came from the Parquet pipeline

3. **Migration Plan**: 
   - Located at `meta/streamlit_parquet_migration_plan.md`
   - Clone approach for safety
   - Reuse existing working code

## Your First Tasks

### 1. Create the Clone
```bash
cp -r streamlit_app/ streamlit_app_parquet/
```

### 2. Study the Golden Source
Open `run_streamgraph_simulation_parquet.py` and understand:
- How it enriches the data with discontinuation flags
- Where it adds `discontinuation_type` categorization
- How it tracks retreatment events

### 3. Start Core Migration
In `streamlit_app_parquet/simulation_runner.py`:
- Import the Parquet generation logic
- Replace JSON serialization with Parquet writing
- Ensure enrichment flags are preserved

### 4. Quick Win - Streamgraphs
Since streamgraphs already work with Parquet:
- Remove the bridge function complexity
- Direct integration should work immediately
- This validates the approach

## Critical Requirements

1. **Don't Reinvent**: The enrichment logic in `run_streamgraph_simulation_parquet.py` is proven. Copy it exactly.

2. **Validate Against References**: The existing streamgraph images show what correct output looks like.

3. **Preserve Both Pipelines**: Keep JSON pipeline working while building Parquet version.

4. **Test Incrementally**: Get one visualization working before moving to the next.

## Expected Outcomes

When complete, the Streamlit app should:
- Show all discontinuation types (not just "discontinued")
- Track retreatment patients properly
- Use the same rich data as standalone visualizations
- Have better performance with Parquet format

## If You Get Stuck

1. Check `run_streamgraph_simulation_parquet.py` - it has the working enrichment logic
2. Reference `meta/patient_state_visualization_definitions_20250522.md` for state mappings
3. Compare outputs with the existing streamgraph images
4. The memory contains the full migration plan

Remember: You're not creating new logic, just unifying two existing pipelines where the Parquet one already works perfectly.

Good luck! 🚀