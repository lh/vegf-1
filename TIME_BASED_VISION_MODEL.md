# Time-Based Vision Change Model

## Core Principles

1. **Vision changes fortnightly** based on disease state and treatment
2. **Vision is measured only at visits** (hidden variable between visits)
3. **Stochastic changes** around means calibrated to annual decline rates
4. **Vision ceiling** based on baseline with absolute maximum

## Vision Change Parameters

### Decline Parameters (per fortnight)
```yaml
vision_decline_fortnightly:
  NAIVE:
    untreated: {mean: -1.2, std: 0.5}  # Rapid decline
    treated: {mean: -0.8, std: 0.4}    # Still declining but slower
  
  STABLE:
    untreated: {mean: -0.3, std: 0.2}  # Slow decline
    treated: {mean: -0.1, std: 0.1}    # Minimal decline
  
  ACTIVE:
    untreated: {mean: -1.5, std: 0.6}  # Significant decline
    treated: {mean: -0.4, std: 0.3}    # Reduced decline
  
  HIGHLY_ACTIVE:
    untreated: {mean: -2.0, std: 0.8}  # Severe decline
    treated: {mean: -0.6, std: 0.4}    # Still declining despite treatment
```

### Improvement Parameters
```yaml
vision_improvement:
  # Probability of improvement (vs just stopping decline)
  improvement_probability:
    STABLE: 0.3      # 30% chance of improvement when treated
    ACTIVE: 0.4      # 40% chance
    HIGHLY_ACTIVE: 0.2  # Only 20% chance in severe disease
  
  # Improvement rate when it occurs (per fortnight)
  improvement_rate:
    STABLE: {mean: 0.5, std: 0.2}
    ACTIVE: {mean: 0.8, std: 0.3}
    HIGHLY_ACTIVE: {mean: 0.6, std: 0.3}
  
  # Maximum improvement duration (fortnights)
  max_improvement_duration: 6  # 3 months = 6 fortnights
```

### Ceiling Parameters
```yaml
vision_ceilings:
  # Individual ceiling as percentage of baseline
  baseline_ceiling_factor: 1.1  # Can improve up to 110% of baseline
  
  # Absolute maximums by baseline range
  absolute_ceiling:
    default: 85  # General maximum
    high_baseline: 95  # If started > 80
    low_baseline: 75   # If started < 50
```

## Implementation Design

### 1. Patient Vision Tracking
```python
class Patient:
    # Current (observable at visits)
    baseline_vision: int
    
    # New time-based tracking
    actual_vision: float  # Continuous value between visits
    vision_ceiling: int   # Individual maximum
    improvement_start_date: Optional[datetime]  # Track improvement window
    is_improving: bool    # Currently in improvement phase
    total_treatments: int  # Track for improvement eligibility
    last_treatment_gap: int  # Days since last treatment (for gap-triggered improvement)
```

### 2. Fortnightly Vision Update Logic
```python
def update_vision_fortnightly(patient, current_date):
    """Update vision every 14 days based on disease state and treatment."""
    
    # Calculate treatment effect with decay
    days_since_injection = patient.days_since_last_injection_at(current_date)
    treatment_effect = calculate_treatment_effect(days_since_injection)
    
    # Check improvement eligibility
    can_improve = (
        patient.total_treatments < 5 and  # Rare after 5 treatments
        (patient.total_treatments == 1 or  # First treatment
         patient.last_treatment_gap > 84)  # After treatment gap
    )
    
    # Check if we should start/stop improvement phase
    if treatment_effect > 0.5 and not patient.is_improving and can_improve:
        # Potentially start improvement (probabilistic)
        if random.random() < improvement_probability[patient.disease_state]:
            patient.is_improving = True
            patient.improvement_start_date = current_date
    
    # Check if improvement window has expired
    if patient.is_improving:
        improvement_duration = (current_date - patient.improvement_start_date).days / 14
        if improvement_duration > max_improvement_duration:
            patient.is_improving = False
    
    # Calculate vision change
    if patient.is_improving and patient.actual_vision < patient.vision_ceiling:
        # Improvement phase
        params = improvement_rate[patient.disease_state]
        change = random.gauss(params['mean'], params['std'])
        change = max(0, change)  # Only positive during improvement
    else:
        # Decline phase - bimodal risk
        base_decline = calculate_gradual_decline(patient, treatment_effect)
        hemorrhage_loss = check_catastrophic_hemorrhage(patient, treatment_effect)
        change = base_decline - hemorrhage_loss
    
    # Apply change with floor/ceiling enforcement
    patient.actual_vision += change
    patient.actual_vision = min(patient.actual_vision, patient.vision_ceiling)
    patient.actual_vision = max(0, patient.actual_vision)  # Absolute floor

def calculate_treatment_effect(days_since_injection):
    """Calculate treatment efficacy with decay."""
    if days_since_injection is None:
        return 0.0
    elif days_since_injection <= 56:  # First 8 weeks - full effect
        return 1.0
    elif days_since_injection <= 84:  # Weeks 8-12 - gradual decline
        return 1.0 - (days_since_injection - 56) / 56
    elif days_since_injection <= 112:  # Weeks 12-16 - faster decline
        return 0.5 - (days_since_injection - 84) / 56
    else:  # Beyond 16 weeks - minimal effect
        return max(0.0, 0.25 - (days_since_injection - 112) / 112)

def calculate_gradual_decline(patient, treatment_effect):
    """Calculate gradual vision decline with treatment effect."""
    # Get base decline rate
    scenario = f"{patient.disease_state}_untreated"
    base_params = vision_decline_fortnightly[scenario]
    
    # Modify by treatment effect
    if treatment_effect > 0:
        treated_params = vision_decline_fortnightly[f"{patient.disease_state}_treated"]
        # Interpolate between treated and untreated based on effect
        mean = (base_params['mean'] * (1 - treatment_effect) + 
                treated_params['mean'] * treatment_effect)
        std = (base_params['std'] * (1 - treatment_effect) + 
               treated_params['std'] * treatment_effect)
    else:
        mean, std = base_params['mean'], base_params['std']
    
    return random.gauss(mean, std)

def check_catastrophic_hemorrhage(patient, treatment_effect):
    """Check for sudden hemorrhage with increasing risk over time."""
    if patient.disease_state not in [DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE]:
        return 0  # Only risk in active disease
    
    # Base risk increases with time since treatment
    days_untreated = patient.days_since_last_injection_at(current_date) or 999
    
    # Risk calculation (these parameters need clinical calibration)
    if days_untreated <= 84:
        base_risk = 0.001  # 0.1% per fortnight when treated
    elif days_untreated <= 168:
        base_risk = 0.005  # 0.5% per fortnight at 3-6 months
    else:
        base_risk = 0.01   # 1% per fortnight beyond 6 months
    
    # Higher risk in highly active disease
    if patient.disease_state == DiseaseState.HIGHLY_ACTIVE:
        base_risk *= 2
    
    # Check for hemorrhage
    if random.random() < base_risk:
        # Catastrophic loss: 10-30 letters
        return random.uniform(10, 30)
    
    return 0
```

### 3. Vision Measurement at Visits
```python
def record_vision_at_visit(patient, visit_date):
    """Record observable vision at visit with measurement noise."""
    # Add measurement noise (±5 letters)
    measurement_noise = random.gauss(0, 2.5)  # 95% within ±5 letters
    measured_vision = patient.actual_vision + measurement_noise
    
    # Round to integer and enforce bounds
    measured_vision = int(round(measured_vision))
    measured_vision = max(0, min(100, measured_vision))
    
    # Record in visit history
    visit_record = {
        'date': visit_date,
        'measured_vision': measured_vision,
        'actual_vision': patient.actual_vision,  # True value for analysis
        'measurement_noise': measurement_noise,
        'is_improving': patient.is_improving
    }
    return visit_record
```

### 4. Vision Floor Discontinuation
```python
# Configuration
vision_discontinuation_config = {
    'vision_threshold': 20,  # Configurable threshold
    'discontinuation_probability': 0.8,  # 80% chance if below threshold
    'grace_period_visits': 2  # Allow 2 visits below threshold before discontinuing
}

def check_vision_discontinuation(patient, measured_vision):
    """Check if treatment should be discontinued due to poor vision."""
    if measured_vision >= vision_discontinuation_config['vision_threshold']:
        # Reset counter if above threshold
        patient.visits_below_threshold = 0
        return False
    
    # Below threshold
    patient.visits_below_threshold += 1
    
    # Check if grace period exceeded
    if patient.visits_below_threshold >= vision_discontinuation_config['grace_period_visits']:
        # Probabilistic discontinuation
        if random.random() < vision_discontinuation_config['discontinuation_probability']:
            patient.discontinuation_reason = 'poor_vision'
            patient.discontinuation_vision = measured_vision
            return True
    
    return False
```

## Calibration Strategy

1. **Annual Decline Rates** (from literature)
   - Untreated active AMD: -15 to -20 letters/year
   - Treated active AMD: -2 to -5 letters/year
   - Stable treated: 0 to -2 letters/year

2. **Convert to Fortnightly**
   - Annual rate / 26 = fortnightly mean
   - Add appropriate variance

3. **Validation Metrics**
   - Mean vision change at 1 year
   - Proportion gaining ≥5 letters
   - Proportion losing ≥15 letters
   - Time to vision stability

## Key Differences from Per-Visit Model

1. **Continuous Progression**: Vision changes every fortnight, not just at visits
2. **Treatment Response**: Realistic 3-month improvement window
3. **Individual Ceilings**: Each patient has personalized maximum vision
4. **Hidden Variables**: True vision state between measurements
5. **New Parameters**: Completely new parameter set, not converted from old

## Summary of Key Features

1. **Bimodal Vision Loss**
   - Gradual decline with treatment effect decay
   - Catastrophic hemorrhage risk increasing over time

2. **Treatment Effect Decay**
   - Full effect for 8 weeks
   - Gradual decline weeks 8-16
   - Minimal effect beyond 16 weeks

3. **Improvement Mechanics**
   - Most likely with first treatment or after gap
   - Rare after 5 treatments
   - Limited to 3-month window

4. **Measurement Realism**
   - ±5 letter measurement noise at visits
   - Hidden true vision between visits
   - Vision floor discontinuation with grace period

5. **Configurable Parameters**
   - Vision threshold for discontinuation
   - Hemorrhage risk rates
   - Treatment effect half-life
   - Individual vision ceilings

## Open Questions

1. **Hemorrhage Risk Calibration**: Need clinical data for accurate risk rates
2. **Treatment Resistance**: Should efficacy decline with repeated treatments?
3. **Age Effects**: Should older patients have different parameters?
4. **Bilateral Disease**: How to model when both eyes are affected?