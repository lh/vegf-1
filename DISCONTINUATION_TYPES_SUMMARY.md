# Discontinuation Types in ABS Simulation

Based on my analysis of the code, the ABS simulation implements the following discontinuation types:

## 1. stable_max_interval (Protocol-based)
- **Trigger**: Patient has been stable at maximum treatment interval
- **Criteria**:
  - Consecutive stable visits: 3 (configurable)
  - Interval weeks: 16 (maximum interval)
  - Probability: 0.2 (20% chance when criteria met)
- **Monitoring Schedule**: Standard monitoring (12, 24, 36 weeks)
- **Recurrence Model**: Lower recurrence rates (planned discontinuation)
- **Reason String**: "stable_max_interval"

## 2. random_administrative (Administrative)
- **Trigger**: Random administrative discontinuation (e.g., insurance, relocation)
- **Criteria**:
  - Annual probability: 0.05 (5% per year)
  - Converted to per-visit probability (~0.7% per visit)
- **Monitoring Schedule**: None (patient lost to follow-up)
- **Recurrence Model**: No monitoring, so no recurrence detection
- **Reason String**: "random_administrative"

## 3. treatment_duration / course_complete_but_not_renewed
- **Trigger**: End of standard treatment course without renewal
- **Criteria**:
  - Threshold weeks: 52 (1 year of treatment)
  - Probability: 0.1 (10% chance after threshold)
- **Monitoring Schedule**: More frequent monitoring (8, 16, 24 weeks)
- **Recurrence Model**: Higher recurrence rates than planned discontinuation
- **Reason String**: "course_complete_but_not_renewed"

## 4. premature (Non-adherence)
- **Trigger**: Premature discontinuation before protocol criteria met
- **Criteria**:
  - Minimum interval weeks: 8
  - Probability factor: 0.05 (base multiplier)
  - Target rate: 0.145 (14.5% overall)
  - Profile multipliers:
    - adherent: 0.2 (rare)
    - average: 1.0 (base rate)
    - non_adherent: 3.0 (3x more likely)
- **Vision Impact**:
  - Mean VA loss: -9.4 letters
  - VA loss standard deviation: 5.0
- **Monitoring Schedule**: More frequent monitoring (8, 16, 24 weeks)
- **Recurrence Model**: Highest recurrence rates
- **Reason String**: "premature"

## Key Implementation Details

### 1. The evaluate_discontinuation method returns a tuple:
```python
(discontinue: bool, reason: str, probability: float, cessation_type: str)
```

### 2. Vision changes are applied immediately after certain discontinuation types:
- Premature discontinuation applies immediate VA loss (mean -9.4 letters)
- Other types don't have immediate vision impact

### 3. Monitoring schedules vary by cessation type:
- stable_max_interval: Standard monitoring (12, 24, 36 weeks)
- premature: More frequent (8, 16, 24 weeks)
- course_complete_but_not_renewed: More frequent (8, 16, 24 weeks)
- random_administrative: No monitoring (lost to follow-up)

### 4. Recurrence models differ by cessation type:
- Each type has different cumulative recurrence rates over time
- PED presence increases recurrence risk by factor of 1.54
- Time-dependent probability calculation using linear interpolation

### 5. Retreatment eligibility:
- Fluid must be detected
- Vision loss of 5+ letters required
- Probability: 0.95 (95% chance when eligible)

### 6. Statistics tracked:
- Total discontinuations by type
- Retreatments by cessation type
- Premature discontinuation rates
- Clinician influence on decisions

## Configuration Location
These parameters are defined in:
`protocols/simulation_configs/enhanced_discontinuation.yaml`

## Usage in Code
The discontinuation logic is primarily in:
1. `simulation/enhanced_discontinuation_manager.py` - Core logic
2. `treat_and_extend_abs.py` - Implementation in ABS simulation