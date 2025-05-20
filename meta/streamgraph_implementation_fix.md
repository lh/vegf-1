# Streamgraph Visualization Implementation Fix

## Problem Statement

The streamgraph visualization for patient states was showing only active and monitoring states, failing to properly display different types of discontinued patients (planned, administrative, duration-based). This was causing an incomplete representation of patient outcomes in the visualization.

## Root Cause Analysis

1. **Missing Discontinuation Flags in Visit Records**:
   - The simulation was not properly setting the `is_discontinuation_visit` and `discontinuation_type` flags in visit records.
   - When a patient was discontinued, the discontinuation state was stored in the patient's `treatment_status` object but not in the specific visit record.

2. **Incorrect State Determination Logic**:
   - The visualization code was looking for explicit discontinuation flags in visit records.
   - Without these flags, all discontinued patients appeared as either active or monitoring.

3. **Data Format Issues**:
   - JSON serialization was causing issues with type preservation, particularly with dates.
   - We needed to use Parquet format to preserve type information.

## Solution Implementation

### 1. Fix Flag Setting in Simulation Code

Fixed `treat_and_extend_abs_fixed.py` to properly set discontinuation flags in visit records:

```python
# When a patient is discontinued
if should_discontinue:
    # Update patient state
    patient.treatment_status["active"] = False
    patient.treatment_status["discontinuation_date"] = event.time
    patient.treatment_status["discontinuation_reason"] = reason
    patient.treatment_status["cessation_type"] = cessation_type
    
    # Mark the most recent visit record as a discontinuation visit
    if patient.history and len(patient.history) > 0:
        latest_visit = patient.history[-1]
        latest_visit['is_discontinuation_visit'] = True
        latest_visit['discontinuation_type'] = cessation_type
```

Same for administrative discontinuations:

```python
# When an administrative discontinuation happens
if not patient.treatment_status["active"] and patient.treatment_status["discontinuation_date"] is None:
    patient.treatment_status["discontinuation_date"] = event.time
    
    # Mark the visit as a discontinuation visit
    if patient.history and len(patient.history) > 0:
        latest_visit = patient.history[-1]
        latest_visit['is_discontinuation_visit'] = True
        latest_visit['discontinuation_type'] = "administrative"
```

### 2. Clean State Determination

Simplified the state determination logic in `create_patient_state_streamgraph.py` to use only explicit flags:

```python
def determine_state(row):
    """
    Determine patient state from visit data using only explicit flags.
    """
    # Check explicit retreatment flag
    if row.get("is_retreatment_visit", False):
        return "retreated"
        
    # Check explicit discontinuation flags
    if row.get("is_discontinuation_visit", False):
        # Get discontinuation type for categorization
        disc_type = row.get("discontinuation_type", "").lower()
        
        # Categorize based on discontinuation type
        if "stable" in disc_type or "planned" in disc_type or "max_interval" in disc_type:
            return "discontinued_planned"
        elif "admin" in disc_type:
            return "discontinued_administrative" 
        elif "duration" in disc_type or "course" in disc_type:
            return "discontinued_duration"
        else:
            # Default to planned if type not recognized
            return "discontinued_planned"
            
    # Check phase for monitoring
    phase = row.get("phase", "").lower()
    if phase == "monitoring":
        return "monitoring"
        
    # Default to active if no other state detected
    return "active"
```

### 3. Parquet-Based Workflow

Created a Parquet-based simulation runner (`run_streamgraph_simulation_parquet.py`) to:
- Run simulations with explicit state flags
- Save results in Parquet format to preserve type information
- Support proper visualization pipeline

## Testing and Verification

Testing showed partial success:

1. The data part of the solution is working correctly:
   - Simulation now properly sets discontinuation flags in visit records
   - State determination logic correctly identifies different patient states
   - Parquet format correctly preserves type information

2. The states are being properly tracked in the data:
   - At month 0: 100% active
   - At month 12: 83% active, 9% discontinued planned, 8% discontinued duration
   - At month 24: 61% active, 2% discontinued planned, 2% discontinued administrative, 3% discontinued duration, 32% monitoring
   - At month 36: 51% active, 1% discontinued planned, 3% discontinued duration, 45% monitoring

## Fixed: Streamgraph Visualization Rendering

We have successfully fixed the visualization rendering to create a proper streamgraph:

1. **Replaced `fill='tonexty'` with `stackgroup='one'`**: 
   - The key issue was that we were using Plotly's `fill='tonexty'` mode, which creates overlapping area charts rather than a true streamgraph.
   - By switching to `stackgroup='one'`, we enable proper stacking of all patient states.

2. **Updated the Plotly trace configuration**:
   ```python
   fig.add_trace(go.Scatter(
       x=months,
       y=values,
       mode='lines',
       line=dict(width=0.5, color=color),
       stackgroup='one',  # This enables proper stacking
       fillcolor=color,
       name=display_name,
       hovertemplate=f"{display_name}: %{{y:.0f}} patients<br>Month: %{{x:.0f}}<extra></extra>"
   ))
   ```

3. **Ensured non-negative y-axis range**:
   ```python
   yaxis=dict(
       gridcolor='lightgrey',
       gridwidth=0.5,
       # Ensure y-axis starts at 0 to show full stacked areas
       rangemode='nonnegative'
   )
   ```

4. **Added comprehensive testing**:
   - Created a test script that verifies the data and visualization.
   - Confirmed that all patient states are properly displayed in the streamgraph.
   - Verified that the stacking is working correctly with real simulation data.

5. **Implemented semantic color scheme**:
   - Updated the color palette to have meaningful associations with patient states:
   ```python
   state_colors = {
       # Active patients - green
       "active": "#1b7a3d",  # Strong green for active treatment
       
       # Retreated patients - lighter green
       "retreated": "#7fbf7f",  # Pale green for retreated patients
       
       # Monitoring patients - blue-green
       "monitoring": "#4682b4",  # Blue for monitoring (non-treatment phases)
       
       # Discontinued patients with semantic color coding:
       # Yellow for planned (expected/desired) discontinuations
       "discontinued_planned": "#ffd700",  # Gold for planned discontinuation
       
       # Red spectrum for undesirable discontinuations:
       "discontinued_administrative": "#ff4500",  # OrangeRed for administrative issues
       "discontinued_premature": "#cd5c5c",  # IndianRed for premature discontinuation
       "discontinued_duration": "#8b0000",  # DarkRed for duration-based discontinuation
   }
   ```

6. **Enhanced state categorization**:
   - Added support for "premature" discontinuation as a separate category
   - Improved the state determination logic to better classify discontinuation types:
   ```python
   # Categorize based on discontinuation type with more granular categories
   if "stable" in disc_type or "planned" in disc_type or "max_interval" in disc_type:
       return "discontinued_planned"
   elif "admin" in disc_type or "administrative" in disc_type:
       return "discontinued_administrative"
   elif "premature" in disc_type or "early" in disc_type:
       return "discontinued_premature"
   elif "duration" in disc_type or "course" in disc_type:
       return "discontinued_duration"
   ```

The updated streamgraph now correctly displays all patient states with proper stacking and meaningful colors, allowing for clear visualization of how patient populations transition between states over time. The color scheme has semantic meaning, with green representing active patients, yellow for planned discontinuations, and red spectrum for the various types of undesirable discontinuations.

## Key Principles

1. **Explicit Flags, Not Inference**: The solution relies on explicit state flags set by the simulation rather than trying to infer states from other data.
2. **Type-Safe Data Format**: Using Parquet format preserves type information, particularly for dates.
3. **Real Data Only**: The visualization uses only real simulation data, never synthetic or placeholder data.
4. **Conservation Principle**: The total patient count is preserved at all time points.
5. **Proper Stacking**: All patient states are properly stacked in the visualization, using Plotly's `stackgroup` parameter.

## Future Work

1. **Advanced Streamgraph Options**: Consider exploring additional streamgraph options like centering the streamgraph around a baseline (`stackgroup='one', groupnorm='percent'`).
2. **Verification Tests**: Add automated tests to verify that visit records contain the proper flags.
3. **Additional State Categories**: Consider adding more granular state categories if needed.
4. **Interactive Controls**: Add interactive filtering by state category.
5. **Color Customization**: Allow customization of color palette for different state categories.