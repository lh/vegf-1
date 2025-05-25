# Patient Explorer Parquet Migration TODO

## Current Status
The Patient Explorer module (`patient_explorer.py`) is currently using the old patient_histories dictionary format and needs to be completely rewritten to use Parquet DataFrames.

## Required Changes

### 1. Function Signature
Change from:
```python
def display_patient_explorer(patient_histories: Dict[str, List[Dict]], simulation_stats: Optional[Dict] = None):
```

To:
```python
def display_patient_explorer(visits_df: pd.DataFrame, simulation_stats: Optional[Dict] = None):
```

### 2. Patient Summary Calculation
Current approach iterates through dictionary. Need to change to DataFrame operations:

```python
# Current: Loop through patient_histories
for patient_id, history in patient_histories.items():
    # Calculate metrics from history list

# New: Use DataFrame groupby and aggregation
patient_summaries = visits_df.groupby('patient_id').agg({
    'vision': ['first', 'last', 'count'],
    'actions': lambda x: sum('injection' in str(a) for a in x),
    'is_discontinuation_visit': 'any',
    'discontinuation_type': 'first'
})
```

### 3. Individual Patient View
Current: Access patient history as list of visits
New: Filter DataFrame by patient_id

```python
# Current
history = patient_histories[selected_patient_id]

# New
patient_visits = visits_df[visits_df['patient_id'] == selected_patient_id].sort_values('time')
```

### 4. Timeline Visualization
Update to use DataFrame columns instead of dictionary keys

### 5. Page Integration
Update `pages/patient_explorer_page.py` to pass DataFrames instead of patient_histories:

```python
# Current
patient_histories = st.session_state["patient_histories"]
display_patient_explorer(patient_histories, results)

# New
visits_df = results.get("visits_df")
if visits_df is not None:
    display_patient_explorer(visits_df, results)
else:
    st.error("No visit data available in Parquet format")
```

## Benefits of Migration
1. Faster aggregations using pandas operations
2. Cleaner code with DataFrame methods
3. Access to enriched data (discontinuation flags, retreatment flags)
4. Consistent with other migrated visualizations

## Testing Checklist
- [ ] Patient filtering works correctly
- [ ] Individual patient timelines display properly
- [ ] Summary statistics match expected values
- [ ] Performance is improved or at least maintained
- [ ] All UI elements remain functional