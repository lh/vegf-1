# Staggered Simulation Refactoring Plan

## Goal
Transform the staggered simulation page to use existing Parquet data viewed through calendar time rather than running a separate simulation.

## Current State Analysis

### What We Have
1. Regular simulation generates Parquet files with:
   - `visits_df`: All visits with actual `date` timestamps
   - `metadata_df`: Simulation parameters including `start_date`
   - Patient enrollment dates (implicit in first visit)
   - Rich discontinuation/retreatment data

2. Existing staggered simulation creates:
   - Time-based enrollment
   - Calendar view of clinic activity
   - Resource utilization metrics

### Key Insight
We can create the staggered view by reprocessing the existing data from a calendar perspective!

## Implementation Plan

### Phase 1: Data Transformation Function
Create `streamlit_app_parquet/staggered_data_processor.py`:

```python
def transform_to_calendar_view(visits_df, metadata_df):
    """
    Transform patient-relative time data to calendar time view.
    
    Returns:
    - calendar_visits_df: Visits with calendar month column
    - monthly_metrics: Aggregated metrics by calendar month
    """
    # Add calendar month column
    visits_df['calendar_month'] = visits_df['date'].dt.to_period('M')
    
    # Calculate metrics by calendar month:
    # - Active patients
    # - New enrollments  
    # - Clinic visits
    # - Discontinuations
    # - Retreatments
```

### Phase 2: Update Staggered Simulation Page

1. **Remove simulation runner code**
   - No need for `run_staggered_simulation()`
   - Use existing Parquet data instead

2. **Add data selector**
   ```python
   # Let user select from existing simulations
   available_sims = get_available_parquet_simulations()
   selected_sim = st.selectbox("Select simulation data", available_sims)
   ```

3. **Load and transform data**
   ```python
   # Load the selected Parquet files
   visits_df, metadata_df, stats_df = load_parquet_data(selected_sim)
   
   # Transform to calendar view
   calendar_data = transform_to_calendar_view(visits_df, metadata_df)
   ```

### Phase 3: Create Calendar-Based Visualizations

1. **Clinic Activity Over Time**
   - X-axis: Calendar months (Jan 2023, Feb 2023, etc.)
   - Y-axis: Number of clinic visits
   - Shows natural ramp-up and steady state

2. **Active Patient Census**
   - Track active vs discontinued patients by calendar month
   - Show enrollment growth curve

3. **Resource Utilization**
   - Daily/weekly visit counts
   - Peak capacity analysis
   - Waiting time estimates (if modeled)

4. **Enrollment Timeline**
   - Gantt-style chart showing patient journeys
   - Color by outcome (active, discontinued, retreated)

### Phase 4: Integration Benefits

1. **Consistent Data**
   - Same patients, same outcomes
   - Just different time perspective

2. **Rich Insights**
   - See seasonal patterns
   - Observe clinic ramp-up
   - Identify capacity constraints

3. **No Duplicate Computation**
   - Reuse existing simulation results
   - Faster page loads
   - Less memory usage

## File Structure

```
streamlit_app_parquet/
├── staggered_data_processor.py    # New: Calendar view transformation
├── pages/
│   └── staggered_simulation_page.py  # Modified: Use Parquet data
├── visualizations/
│   └── calendar_viz.py            # New: Calendar-based charts
```

## Implementation Steps

1. **Create data processor** (30 min)
   - Transform visits to calendar view
   - Aggregate monthly metrics

2. **Update page logic** (45 min)
   - Remove simulation code
   - Add Parquet data loading
   - Integrate transformations

3. **Create visualizations** (1 hour)
   - Clinic activity chart
   - Patient census chart
   - Enrollment timeline

4. **Testing** (30 min)
   - Verify calculations
   - Check edge cases
   - Performance testing

## Benefits

1. **User Experience**
   - Instant results (no simulation wait)
   - Consistent with main simulation
   - Richer insights from same data

2. **Technical**
   - Simpler codebase
   - Reuses existing Parquet pipeline
   - Better performance

3. **Scientific**
   - Same underlying patient data
   - Just different analytical lens
   - Maintains data integrity

## Success Criteria

- [ ] Page loads existing Parquet data
- [ ] Calendar view shows realistic clinic patterns
- [ ] Enrollment ramp-up is visible
- [ ] All discontinuation types are tracked
- [ ] Performance is fast (<2s load time)
- [ ] Visualizations follow established style guide