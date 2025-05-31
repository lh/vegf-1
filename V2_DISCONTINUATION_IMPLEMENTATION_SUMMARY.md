# V2 Discontinuation System Implementation Summary
*Date: 27 May 2025*

## Overview

Successfully implemented a comprehensive discontinuation system for the V2 AMD simulation, upgrading from a simple binary (discontinued/active) system to a rich 6-category model based on clinical data and real-world experience.

## Implementation Details

### ✅ **Phase 1: Core Infrastructure**

1. **DiscontinuationProfile class** (`simulation_v2/core/discontinuation_profile.py`)
   - YAML loading/saving support
   - Validation methods
   - Default profile creation

2. **Updated Patient class** (`simulation_v2/core/patient.py`)
   - Added tracking fields for discontinuation
   - Enhanced discontinue() method
   - First visit date tracking

3. **V2DiscontinuationManager** (`simulation_v2/core/discontinuation_manager.py`)
   - Evaluates 6 discontinuation categories in priority order
   - Handles monitoring schedules
   - Manages retreatment decisions
   - Tracks comprehensive statistics

4. **Default Profiles** (in `simulation_v2/profiles/discontinuation/`)
   - `ideal.yaml` - Perfect world scenario
   - `nhs_1.yaml` - Real-world UK parameters
   - README with documentation

5. **Enhanced ABS Engine** (`simulation_v2/engines/abs_engine_v2.py`)
   - Integrates discontinuation manager
   - Handles monitoring visits
   - Supports retreatment

6. **Updated ParquetWriter** 
   - Captures new discontinuation fields
   - Stores retreatment counts

## Six Discontinuation Categories

1. **`stable_max_interval`** (Protocol-based)
   - Criteria: 3 consecutive stable visits at 16-week intervals
   - Probability: 20% when criteria met
   - Monitoring: Standard (12, 24, 36 weeks)
   - Recurrence: 13% at 1yr, 40% at 3yr, 65% at 5yr

2. **`poor_response`** (Treatment failure)
   - Criteria: BCVA < 15 letters on 2 consecutive visits
   - Monitoring: None (patient discharged)
   - Based on UK funding body criteria

3. **`premature`** (Patient-initiated)
   - Criteria: Good vision (>20 letters), minimum 8-week interval
   - Target rate: 14.5% (based on real Eylea data analysis)
   - Impact: -9.4 letters vision loss (SD 5.0)
   - Monitoring: Frequent (8, 16, 24 weeks)

4. **`system_discontinuation`** (Administrative barriers)
   - Probability: 5% annual
   - Monitoring: None (lost to follow-up)
   - Represents insurance loss, relocation, admin errors

5. **`reauthorization_failure`** (Funding lapse)
   - Criteria: After 52 weeks treatment
   - Probability: 10% after threshold
   - Represents forgotten reauthorization at funding period end

6. **`mortality`** (Patient death)
   - Rate: 20/1000 annually (configurable)
   - No monitoring or retreatment

## Test Results Demonstrate Impact

### Ideal Profile (no system failures):
- 41.5% discontinuation rate
- 73.1 letter mean final vision
- 10.1 injections per patient
- Mostly stable discontinuations (48.2%) and mortality

### NHS_1 Profile (real-world):
- 91.0% discontinuation rate
- 70.3 letter mean final vision (2.8 letters worse)
- 7.6 injections per patient
- Dominated by reauthorization failures (43.4%)

## Key Design Decisions

1. **Separate from protocol configuration** - Discontinuation profiles are independent of treatment protocols
2. **Profile-based system** - Easy to create and share different scenarios
3. **Priority-ordered evaluation** - Ensures clinical logic (e.g., mortality checked first)
4. **Data-driven parameters** - Based on clinical studies (Arendt, Aslanis, Artiaga) and real-world analysis
5. **Configurable mortality** - Currently 2% annual, awaiting further analysis

## Files Created/Modified

### New Files:
- `simulation_v2/core/discontinuation_profile.py`
- `simulation_v2/core/discontinuation_manager.py`
- `simulation_v2/engines/abs_engine_v2.py`
- `simulation_v2/profiles/discontinuation/ideal.yaml`
- `simulation_v2/profiles/discontinuation/nhs_1.yaml`
- `simulation_v2/profiles/discontinuation/README.md`
- `test_v2_discontinuation.py`

### Modified Files:
- `simulation_v2/core/patient.py` - Added discontinuation tracking fields
- `streamlit_app_v2/core/storage/writer.py` - Added new fields to parquet output

## Remaining Work

1. **Update streamgraph visualization** - Currently shows 2 states, needs to show all 6
2. **Create additional profiles** - US Medicare, Clinical Trial, etc.
3. **Enhance retreatment logic** - Currently simplified
4. **Add clinician profiles** - Deferred per discussion

## Clinical Data Sources

- **Arendt study**: Protocol-based discontinuation outcomes
- **Aslanis study**: Premature discontinuation and PED impact  
- **Artiaga study**: Long-term (5yr) recurrence data
- **Eylea analysis**: Real-world premature discontinuation rate (14.5%)
- **NICE/RCOphth guidance**: Poor response criteria (15 letters)
- **Clinical experience**: Administrative and reauthorization failure rates

## Usage Example

```python
from simulation_v2.core.discontinuation_profile import DiscontinuationProfile
from simulation_v2.engines.abs_engine_v2 import ABSEngineV2

# Load profile
profile = DiscontinuationProfile.from_yaml("profiles/discontinuation/nhs_1.yaml")

# Create engine with profile
engine = ABSEngineV2(
    disease_model=disease_model,
    protocol=protocol,
    n_patients=1000,
    discontinuation_profile=profile
)

# Run simulation
results = engine.run(duration_years=5.0)

# Access discontinuation statistics
print(results.discontinuation_stats)
```

## Validation

The test script (`test_v2_discontinuation.py`) validates:
- All 6 discontinuation types function correctly
- Profiles load from YAML successfully
- Statistics track accurately
- Vision impacts apply correctly
- Meaningful differences between profiles

The system is ready for production use, pending streamgraph visualization updates.