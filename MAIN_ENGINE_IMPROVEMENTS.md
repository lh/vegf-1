# Main Simulation Engine Improvements

## Overview

Based on our heterogeneity research, here are concrete, testable improvements for the main APE.py simulation engine that maintain simplicity while adding clinical realism.

## Priority 1: Core Clinical Features (Quick Wins)

### 1. Loading Phase Implementation
**What**: First 3 injections at monthly intervals, then switch to protocol interval
**Why**: Clinical protocols (VIEW, HAWK/HARRIER) show ~7 injections in Year 1
**Implementation**:
```python
# In patient simulation logic
if injection_count < 3:
    next_interval = 28  # days (monthly)
else:
    next_interval = protocol_interval
```
**Testing**: Run aflibercept protocol, should see ~7 injections in Year 1

### 2. Time-Based Discontinuation
**What**: Cumulative probability of stopping treatment over time
**Why**: Real-world shows 12-15% Year 1, 45-50% by Year 5
**Implementation**:
```python
# Annual discontinuation probabilities (not cumulative)
discontinuation_prob = {
    1: 0.125,   # 12.5% in Year 1
    2: 0.15,    # Additional 15% in Year 2
    3: 0.12,    # Additional 12% in Year 3
    4: 0.08,    # Additional 8% in Year 4
    5: 0.075    # Additional 7.5% in Year 5
}

# At each year boundary, check discontinuation
if random.random() < discontinuation_prob.get(year, 0.05):
    patient.discontinue(reason="time_based")
```
**Testing**: Track discontinuation rates, should match clinical targets

### 3. Response-Based Vision Changes
**What**: Initial gain, then maintenance, then gradual decline
**Why**: Current linear decline doesn't match clinical patterns
**Implementation**:
```python
def get_vision_change(months_since_start, baseline_vision):
    if months_since_start <= 3:
        # Loading phase: rapid improvement
        return random.gauss(3.0, 1.0)  # +3 letters/month
    elif months_since_start <= 12:
        # Year 1: continued improvement
        return random.gauss(0.5, 0.5)  # +0.5 letters/month
    elif months_since_start <= 24:
        # Year 2: maintenance
        return random.gauss(0, 0.5)    # Stable
    else:
        # Year 3+: gradual decline
        return random.gauss(-0.2, 0.3) # -0.2 letters/month
```
**Testing**: Plot vision trajectories, should show initial gain then decline

## Priority 2: Simple Heterogeneity (Medium Complexity)

### 4. Baseline Vision Distribution
**What**: Sample from realistic distribution, not just uniform
**Why**: Clinical trials show normal distribution around 55 letters
**Implementation**:
```python
# Instead of uniform distribution
baseline_vision = random.gauss(55, 15)
baseline_vision = max(25, min(85, baseline_vision))  # Clamp to range
```
**Testing**: Plot baseline distribution, should be bell curve

### 5. Response Magnitude Variability
**What**: Some patients are "good responders", others "poor responders"
**Why**: Seven-UP showed patient-specific decline rates
**Implementation**:
```python
# Assign response type at patient creation
response_types = {
    'good': (0.3, 1.2),      # 30% of patients, 120% of mean response
    'average': (0.5, 1.0),   # 50% of patients, 100% of mean response  
    'poor': (0.2, 0.6)       # 20% of patients, 60% of mean response
}

# Apply multiplier to all vision changes
vision_change = base_change * patient.response_multiplier
```
**Testing**: Track SD of vision changes, should increase over time

### 6. SASH-Specific Discontinuation
**What**: Model inappropriate discontinuation when vision is "good enough"
**Why**: SASH data shows 1.3% clinical error rate
**Implementation**:
```python
# Check at each visit
if vision >= 70:  # Excellent vision
    if random.random() < 0.004:  # 0.4% chance
        patient.discontinue(reason="too_good_to_stop")
        patient.expected_loss = -12.6  # letters over next year
elif vision >= 50 and vision < 70:  # Good vision
    if random.random() < 0.0024:  # 0.24% chance
        patient.discontinue(reason="good_enough")
        patient.expected_loss = -7.3  # letters over next year
```
**Testing**: Track inappropriate stops, verify vision loss patterns

## Priority 3: Enhanced Features (Lower Priority)

### 7. Visit Noise
**What**: ±3 letter measurement variability
**Why**: Real VA measurements have noise
**Implementation**:
```python
measured_vision = true_vision + random.gauss(0, 3)
```

### 8. Treatment Burden Score
**What**: Track cumulative burden affecting discontinuation
**Why**: Frequent injections increase dropout
**Implementation**:
```python
burden_score += 1.0 / interval_days  # Higher score for frequent visits
if burden_score > threshold:
    discontinuation_prob *= 1.5
```

## Testing Strategy

### Quick UI Tests (in APE.py)
1. **Loading Phase**: Run aflibercept protocol, check Year 1 injections (expect ~7)
2. **Discontinuation**: Run 1000 patients, check discontinuation graph
3. **Vision Trajectory**: Check individual patient plots for gain→decline pattern

### Script-Based Validation
```python
# Create test script: test_improvements.py
from simulation import run_with_improvements

# Test 1: Injection frequency
results = run_with_improvements(n_patients=1000, protocol='aflibercept')
year1_injections = calculate_year1_injections(results)
assert 6.5 <= year1_injections.mean() <= 7.5, f"Expected ~7, got {year1_injections.mean()}"

# Test 2: Discontinuation rates
discontinuation_by_year = calculate_discontinuation_rates(results)
assert 0.10 <= discontinuation_by_year[1] <= 0.15, "Year 1 discontinuation out of range"

# Test 3: Vision outcomes
year1_changes = calculate_vision_changes(results, year=1)
assert 5 <= year1_changes.mean() <= 10, "Year 1 vision gain out of range"
assert 12 <= year1_changes.std() <= 18, "Year 1 SD out of range"
```

## Implementation Order

1. **Week 1**: Loading phase + Response-based vision (biggest impact)
2. **Week 2**: Time-based discontinuation
3. **Week 3**: Simple heterogeneity (response types)
4. **Week 4**: SASH-specific patterns
5. **Later**: Enhanced features as time permits

## Success Metrics

Target clinical match rate of >60% on:
- Year 1 mean change: 8.4 letters (currently 0.4)
- Year 1 injections: 7.0 (currently 5.5)
- Year 1 discontinuation: 12.5% (currently 0%)
- Year 5 discontinuation: 47.5% (currently 0%)

## Conclusion

These improvements maintain APE.py's simplicity while adding essential clinical realism. Each feature is independently testable and provides clear value. The implementation is straightforward without the complexity of the full heterogeneity framework.