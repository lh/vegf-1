# Serialization Points Analysis

**Generated**: 2025-05-25  
**Purpose**: Identify all points where data is serialized/deserialized

## Primary Serialization Points

### 1. Parquet Save (streamlit_app_parquet/simulation_runner.py)

**Function**: `save_results_as_parquet()`
- Line 751: Function definition
- Line 887: `visits_df.to_parquet()`
- Line 888: `metadata_df.to_parquet()`
- Line 889: `stats_df.to_parquet()`

**Current Handling**: 
- Added enum detection and conversion (lines 858-869)
- Converts enum.name to string for any Enum type
- This is a band-aid fix

### 2. Parquet Load Points

#### a. Calendar Time Analysis (pages/5_Calendar_Time_Analysis.py)
- Loads visit data for calendar transformation
- Reads disease_state but doesn't use it directly

#### b. Patient Explorer (patient_explorer.py)
- Displays disease_state in patient details
- Would show enum representation without fix

#### c. Simulation Results Loading
- `simulation_runner.py` lines 669-682
- Loads parquet files back into DataFrames
- No deserialization of strings back to enums

#### d. Dashboard Visualizations
- Various charts may use disease_state
- Currently expect strings

## Secondary Serialization Points

### 1. JSON Serialization (deprecated)
- Old streamlit_app used JSON
- Had similar enum issues
- Now removed from parquet version

### 2. Database Storage
- Some results may go to SQLite
- Would have same enum issues

### 3. Export Functions
- CSV export would need string conversion
- R integration expects strings

## Data Flow Analysis

```
1. Simulation generates data
   ├─ Clinical Model → DiseaseState enum
   └─ Simulation logic → 'active'/'stable' strings

2. Data collection
   ├─ ABS: visit_record['disease_state'] = string (from fixed versions)
   └─ DES: visit_record['disease_state'] = string (hardcoded)

3. Save to Parquet
   ├─ Regular sims: strings → parquet (works)
   └─ Staggered sims: enums → parquet (fails without conversion)

4. Load from Parquet
   └─ Always loads as strings (no deserialization)

5. Display/Analysis
   └─ Everything expects strings
```

## Key Insights

1. **Most paths already use strings** - The enum issue is an edge case
2. **No deserialization exists** - We never convert strings back to enums
3. **One-way conversion** - Enum → String, never String → Enum
4. **Visualization expects strings** - All downstream code assumes strings

## Critical Questions

1. **Why do staggered simulations use enums?**
   - They use base simulation classes
   - Which use patient_state.process_visit()
   - Which uses clinical_model output directly

2. **Why don't regular simulations have this issue?**
   - They use "fixed" versions
   - Which bypass clinical model for disease_state
   - Directly assign strings based on fluid detection

3. **Is the clinical model even being used correctly?**
   - Its sophisticated state model is bypassed
   - Only uses 2 of 4 possible states
   - State transitions are ignored

## Recommendations

1. **Short term**: Keep enum conversion at save point
2. **Medium term**: Decide on canonical representation
3. **Long term**: Fix the architectural issue where clinical model is bypassed