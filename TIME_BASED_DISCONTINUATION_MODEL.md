# Time-Based Discontinuation Model

## Core Principles

1. **Discontinuation checks happen ONLY at visits** (not fortnightly)
2. **Multiple discontinuation reasons** tracked explicitly
3. **All parameters externalized** to configuration files
4. **Reason-specific logic** for each discontinuation type

## Discontinuation Reasons

### 1. Death
- Natural mortality risk based on age and time
- May have disease-specific mortality adjustment

### 2. Attrition
- General loss to follow-up
- May increase with treatment duration or burden

### 3. Administrative Error
- Scheduling errors, insurance issues, clinic closures
- Generally constant low probability

### 4. Treatment Error (Clinical Decision)
- Physician decides treatment no longer beneficial
- Based on lack of response or stable disease

### 5. Continued Deterioration
- Vision continues declining despite treatment
- Tracked over multiple visits

### 6. Poor Vision
- Vision below threshold (e.g., 20 letters)
- May have grace period before discontinuation

## Implementation Design

### Discontinuation Parameters (YAML)
```yaml
discontinuation_parameters:
  # Death parameters
  death:
    base_annual_mortality: 0.02  # 2% per year base rate
    age_adjustment_per_decade: 1.5  # 50% increase per decade over 70
    disease_mortality_multiplier:
      STABLE: 1.0
      ACTIVE: 1.1
      HIGHLY_ACTIVE: 1.2
  
  # Attrition parameters
  attrition:
    base_probability_per_visit: 0.01  # 1% per visit
    time_adjustment:
      # Increase with treatment duration
      months_0_12: 1.0
      months_12_24: 1.2
      months_24_plus: 1.5
    injection_burden_adjustment:
      # Increase with injection frequency
      injections_per_year_0_6: 1.0
      injections_per_year_6_12: 1.2
      injections_per_year_12_plus: 1.5
  
  # Administrative error
  administrative:
    probability_per_visit: 0.005  # 0.5% constant
  
  # Treatment error (clinical decision)
  treatment_decision:
    stable_disease_visits_threshold: 6  # After 6 stable visits
    stable_discontinuation_probability: 0.2
    no_improvement_visits_threshold: 4
    no_improvement_probability: 0.15
  
  # Continued deterioration
  deterioration:
    vision_loss_threshold: -10  # Lost 10+ letters from baseline
    visits_with_loss_threshold: 3  # Over 3 visits
    discontinuation_probability: 0.7
  
  # Poor vision (already defined in vision model)
  poor_vision:
    vision_threshold: 20
    discontinuation_probability: 0.8
    grace_period_visits: 2
```

### Discontinuation Check Logic
```python
class DiscontinuationChecker:
    def __init__(self, params: dict):
        self.params = params
        
    def check_at_visit(self, patient, visit_date, measured_vision):
        """Check all discontinuation reasons at visit."""
        reasons = []
        
        # 1. Death check
        if self._check_death(patient, visit_date):
            reasons.append('death')
            
        # 2. Attrition check
        if self._check_attrition(patient, visit_date):
            reasons.append('attrition')
            
        # 3. Administrative error
        if self._check_administrative():
            reasons.append('administrative')
            
        # 4. Treatment decision
        if self._check_treatment_decision(patient):
            reasons.append('treatment_decision')
            
        # 5. Continued deterioration
        if self._check_deterioration(patient, measured_vision):
            reasons.append('deterioration')
            
        # 6. Poor vision
        if self._check_poor_vision(patient, measured_vision):
            reasons.append('poor_vision')
            
        # Return first reason (priority order) or None
        return reasons[0] if reasons else None
    
    def _check_death(self, patient, visit_date):
        """Check mortality risk."""
        # Calculate annual mortality based on age
        age = patient.age_at(visit_date)
        decades_over_70 = max(0, (age - 70) / 10)
        
        params = self.params['death']
        annual_mortality = (params['base_annual_mortality'] * 
                           (params['age_adjustment_per_decade'] ** decades_over_70))
        
        # Adjust for disease state
        disease_multiplier = params['disease_mortality_multiplier'].get(
            patient.current_state.name, 1.0
        )
        annual_mortality *= disease_multiplier
        
        # Convert to per-visit probability
        days_since_last_visit = (visit_date - patient.last_visit_date).days
        visit_mortality = 1 - (1 - annual_mortality) ** (days_since_last_visit / 365.25)
        
        return random.random() < visit_mortality
    
    def _check_attrition(self, patient, visit_date):
        """Check general loss to follow-up."""
        params = self.params['attrition']
        base_prob = params['base_probability_per_visit']
        
        # Time adjustment
        months_treated = patient.months_since_first_treatment(visit_date)
        if months_treated >= 24:
            time_mult = params['time_adjustment']['months_24_plus']
        elif months_treated >= 12:
            time_mult = params['time_adjustment']['months_12_24']
        else:
            time_mult = params['time_adjustment']['months_0_12']
        
        # Injection burden adjustment
        injections_per_year = patient.injection_rate_last_year(visit_date)
        if injections_per_year >= 12:
            burden_mult = params['injection_burden_adjustment']['injections_per_year_12_plus']
        elif injections_per_year >= 6:
            burden_mult = params['injection_burden_adjustment']['injections_per_year_6_12']
        else:
            burden_mult = params['injection_burden_adjustment']['injections_per_year_0_6']
        
        final_prob = base_prob * time_mult * burden_mult
        return random.random() < final_prob
    
    def _check_administrative(self):
        """Check administrative error."""
        return random.random() < self.params['administrative']['probability_per_visit']
    
    def _check_treatment_decision(self, patient):
        """Check clinical decision to stop treatment."""
        params = self.params['treatment_decision']
        
        # Check if stable for too long
        if patient.consecutive_stable_visits >= params['stable_disease_visits_threshold']:
            if random.random() < params['stable_discontinuation_probability']:
                return True
        
        # Check if no improvement
        if (patient.visits_without_improvement >= params['no_improvement_visits_threshold'] and
            patient.total_injections > 3):  # After initial loading phase
            if random.random() < params['no_improvement_probability']:
                return True
                
        return False
    
    def _check_deterioration(self, patient, measured_vision):
        """Check continued deterioration."""
        params = self.params['deterioration']
        
        vision_change = measured_vision - patient.baseline_vision
        
        if vision_change <= params['vision_loss_threshold']:
            patient.visits_with_significant_loss += 1
            
            if patient.visits_with_significant_loss >= params['visits_with_loss_threshold']:
                if random.random() < params['discontinuation_probability']:
                    return True
        else:
            # Reset counter if vision improved
            patient.visits_with_significant_loss = 0
            
        return False
    
    def _check_poor_vision(self, patient, measured_vision):
        """Check vision floor (delegated to vision model)."""
        # This is handled by the vision model's check_vision_discontinuation
        # Included here for completeness
        return False
```

### Patient Tracking Requirements
```python
# Additional patient attributes needed
class Patient:
    # Existing attributes...
    
    # For discontinuation tracking
    age: int  # Or birth_date to calculate age
    last_visit_date: datetime
    consecutive_stable_visits: int
    visits_without_improvement: int
    visits_with_significant_loss: int
    
    # For calculating rates
    first_treatment_date: datetime
    injection_count_by_date: Dict[datetime, int]
    
    # Discontinuation outcome
    is_discontinued: bool
    discontinuation_date: Optional[datetime]
    discontinuation_reason: Optional[str]
```

## Key Design Decisions

1. **Priority Order**: Death → Attrition → Administrative → Clinical → Deterioration → Poor Vision
2. **Single Reason**: Patient discontinues for first matching reason only
3. **Visit-Based**: All checks happen at visits, not between
4. **State Tracking**: Patient must track various counters for decision logic
5. **Configurable**: All thresholds and probabilities in external config

## Open Questions

1. **Competing Risks**: Should we check all reasons and pick one, or stop at first match?
2. **Reason Interactions**: Should poor vision increase attrition probability?
3. **Recovery**: Can patients who meet criteria sometimes continue anyway?
4. **Documentation**: How much detail to track about discontinuation decision?