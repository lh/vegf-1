# Time Granularity Analysis for Disease Progression

## Current Clinical Reality

### Protocol Intervals
All treat-and-extend protocols use 2-week increments:
- **Minimum interval**: 28 days (4 weeks)
- **Maximum interval**: 112 days (16 weeks)
- **Extension increment**: 14 days (2 weeks)
- **Shortening increment**: 14 days (2 weeks)

### Actual Visit Intervals
- 4 weeks (28 days)
- 6 weeks (42 days)
- 8 weeks (56 days)
- 10 weeks (70 days)
- 12 weeks (84 days)
- 14 weeks (98 days)
- 16 weeks (112 days)

## Options Analysis

### Option 1: Monthly Updates (30 days)
**Pros:**
- Simple to implement and explain
- Aligns with clinical reporting periods
- Lower computational cost

**Cons:**
- Misaligned with 2-week protocol increments
- 28-day visits don't align with 30-day months
- Requires interpolation for most intervals

### Option 2: Fortnightly Updates (14 days)
**Pros:**
- Perfect alignment with ALL protocol intervals
- No interpolation needed
- Captures treatment effect decay more accurately
- Natural fit with extension/shortening logic

**Cons:**
- ~2x computational cost vs monthly
- 26 updates per year vs 12

### Option 3: Weekly Updates (7 days)
**Pros:**
- Even finer granularity
- Could model more complex patterns

**Cons:**
- 52 updates per year (4x monthly cost)
- Unnecessary precision for 2-week minimum increments
- No clinical rationale

### Option 4: Daily Updates (Current)
**Pros:**
- Maximum precision
- Already implemented for visit scheduling

**Cons:**
- 365 updates per year
- Computational overkill for disease progression
- Complex to implement efficiently

## Recommendation: Fortnightly (14-day) Updates

### Rationale
1. **Perfect Protocol Alignment**: Every visit interval is a multiple of 14 days
2. **Clinical Validity**: 2-week periods are clinically meaningful
3. **Computational Efficiency**: Only 26 updates/year vs 365 daily
4. **Implementation Simplicity**: No interpolation or edge cases

### Implementation Approach

```python
class DiseaseModelTimeBased:
    UPDATE_INTERVAL_DAYS = 14  # Fortnightly
    
    def should_update(self, current_date, last_update_date):
        """Check if 14 days have passed since last update"""
        return (current_date - last_update_date).days >= self.UPDATE_INTERVAL_DAYS
    
    def apply_fortnightly_transition(self, current_state, treated_recently):
        """Apply 14-day transition probability"""
        # Use fortnightly_transitions instead of monthly
        base_prob = self.fortnightly_transitions[current_state]
        
        # Treatment effect based on how recently treated
        if treated_recently:
            # Apply treatment multipliers
            ...
```

### Parameter Conversion

To convert existing per-visit probabilities to fortnightly:

```python
def visits_per_fortnight_by_state(state):
    """Estimate visits per 2 weeks for each disease state"""
    if state == "STABLE":
        return 14 / 84  # Every 12 weeks = 0.167 visits/fortnight
    elif state == "ACTIVE": 
        return 14 / 42  # Every 6 weeks = 0.333 visits/fortnight
    elif state == "HIGHLY_ACTIVE":
        return 14 / 28  # Every 4 weeks = 0.5 visits/fortnight
        
def convert_to_fortnightly(per_visit_prob, disease_state):
    """Convert per-visit to per-fortnight probability"""
    visits_per_fortnight = visits_per_fortnight_by_state(disease_state)
    
    # Solve: per_visit = 1 - (1 - fortnightly)^(1/visits_per_fortnight)
    fortnightly = 1 - (1 - per_visit_prob)**visits_per_fortnight
    return fortnightly
```

### Treatment Effect Modeling

With 14-day updates, we can model treatment decay more naturally:

```python
def treatment_efficacy(days_since_injection):
    """Exponential decay with half-life"""
    HALF_LIFE_DAYS = 56  # 8 weeks (configurable)
    return 0.5 ** (days_since_injection / HALF_LIFE_DAYS)
```

## Impact on Simulation

### Current Daily Loop
```python
while current_date <= end_date:
    # Process visits for today
    # Advance by 1 day
```

### Proposed Fortnightly Updates
```python
while current_date <= end_date:
    # Daily: Process visits and arrivals
    
    # Fortnightly: Update disease states
    if (current_date - start_date).days % 14 == 0:
        update_all_patient_states(current_date)
    
    # Advance by 1 day
```

## Conclusion

**Fortnightly (14-day) updates** provide the optimal balance of:
- Clinical accuracy
- Computational efficiency  
- Implementation simplicity
- Perfect protocol alignment

This avoids the interpolation issues of monthly updates while being much more efficient than daily disease updates.

---
**Status**: Decision Made - Use Fortnightly Updates