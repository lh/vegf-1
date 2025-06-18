# ABS Heterogeneity: Algorithm Reconciliation

Date: 2025-01-18  
Purpose: Reconcile algorithm differences between planning documents

## Identified Inconsistencies

### 1. Vision Update Algorithm

**In Discussion Document**:
```python
def update_vision(self, treatment_given, time_elapsed):
    treatment_benefit = 0
    if treatment_given:
        treatment_benefit = (
            5.0 * self.treatment_responder_type * 
            (1 - self.vision/self.max_achievable_va)  # ceiling effect
        )
    
    progression = -0.5 * self.disease_aggressiveness * time_elapsed
    noise = normal(0, 2)
    catastrophic_drop = 0
    if random() < 0.001 * time_elapsed:
        catastrophic_drop = -uniform(10, 30)
    
    self.vision += treatment_benefit + progression + noise + catastrophic_drop
    self.vision = clip(self.vision, 0, 85)
```

**In Specification Document**:
```python
def update_vision(current_va: float, treatment: bool, weeks: float) -> float:
    if treatment:
        base_effect = 5.0
        ceiling_factor = 1 - (current_va / max_achievable_va)
        treatment_benefit = base_effect * treatment_responder_type * ceiling_factor
    else:
        treatment_benefit = 0
    
    base_progression = -0.5
    progression = base_progression * disease_aggressiveness * weeks
    
    # Additional in spec: Treatment resistance
    if treatment:
        treatments_received += 1
        resistance_factor = exp(-resistance_rate * treatments_received)
        treatment_benefit *= resistance_factor
    
    noise = normal(0, 2)
    
    catastrophic_drop = 0
    for event in catastrophic_events:
        if random() < event.probability * weeks:
            catastrophic_drop = sample_distribution(event.impact)
    
    new_va = current_va + treatment_benefit + progression + noise + catastrophic_drop
    return clip(new_va, 0, 85)
```

**Reconciled Algorithm**:
```python
def update_vision(self, treatment_given: bool, weeks_elapsed: float) -> float:
    """
    Update vision with heterogeneous response.
    
    Combines all elements from both documents.
    """
    current_va = self.vision
    
    # 1. Treatment effect (heterogeneous)
    treatment_benefit = 0
    if treatment_given:
        # Base effect with responder type
        base_effect = 5.0
        ceiling_factor = 1 - (current_va / self.max_achievable_va)
        treatment_benefit = base_effect * self.treatment_responder_type * ceiling_factor
        
        # Apply treatment resistance (tachyphylaxis)
        self.treatments_received += 1
        resistance_factor = np.exp(-self.resistance_rate * self.treatments_received)
        treatment_benefit *= resistance_factor
    
    # 2. Disease progression (heterogeneous)
    base_progression = -0.5  # letters per week
    progression = base_progression * self.disease_aggressiveness * weeks_elapsed
    
    # 3. Measurement noise
    noise = self.rng.normal(0, 2)
    
    # 4. Catastrophic events (rare)
    catastrophic_drop = 0
    for event_type, event_config in self.catastrophic_events.items():
        prob_per_week = event_config['probability_per_month'] / 4.33
        if self.rng.random() < prob_per_week * weeks_elapsed:
            impact_dist = event_config['vision_impact']
            if impact_dist['distribution'] == 'uniform':
                catastrophic_drop = self.rng.uniform(
                    impact_dist['min'], 
                    impact_dist['max']
                )
            # Log catastrophic event
            self.catastrophic_event_history.append({
                'week': self.current_week,
                'event': event_type,
                'impact': catastrophic_drop
            })
    
    # 5. Apply all changes
    new_va = current_va + treatment_benefit + progression + noise + catastrophic_drop
    
    # 6. Enforce bounds
    self.vision = np.clip(new_va, 0, 85)
    
    return self.vision
```

### 2. Patient Initialization

**In Discussion Document**:
```python
def __init__(self):
    self.baseline_va = normal(55, 20)
    self.treatment_responder_type = lognormal(1, 0.4)
    self.disease_aggressiveness = lognormal(1, 0.5)
    self.max_achievable_va = min(85, self.baseline_va + normal(10, 15))
    
    if self.baseline_va > 70:
        self.treatment_responder_type *= 1.3
        self.disease_aggressiveness *= 0.7
```

**In Specification Document**:
Shows algorithm with trajectory class assignment first, then parameter generation.

**Reconciled Approach**:
```python
def create_heterogeneous_patient(self, patient_id: str, baseline_va: float) -> HeterogeneousPatient:
    """
    Create patient with heterogeneous characteristics.
    
    Reconciles both initialization approaches.
    """
    # 1. Assign trajectory class
    trajectory_class = self.heterogeneity_manager.assign_trajectory_class()
    
    # 2. Get base parameters for trajectory class
    class_params = self.trajectory_classes[trajectory_class]['parameters']
    
    # 3. Generate patient-specific values from class distributions
    characteristics = {}
    for param_name, param_config in class_params.items():
        base_value = self._sample_distribution(param_config)
        characteristics[param_name] = base_value
    
    # 4. Apply correlations with baseline VA
    # This reconciles the correlation approach from both documents
    if baseline_va > 70:  # High baseline
        characteristics['treatment_effect_multiplier'] *= 1.3
        characteristics['disease_progression_multiplier'] *= 0.7
    elif baseline_va < 40:  # Low baseline
        characteristics['treatment_effect_multiplier'] *= 0.8
        characteristics['disease_progression_multiplier'] *= 1.2
    
    # 5. Calculate max achievable VA
    offset = self.rng.normal(10, 15)
    characteristics['max_achievable_va'] = min(85, baseline_va + offset)
    
    # 6. Add trajectory class to characteristics
    characteristics['trajectory_class'] = trajectory_class
    
    # 7. Initialize treatment tracking
    characteristics['treatments_received'] = 0
    characteristics['resistance_rate'] = self._sample_distribution(
        self.patient_parameters['resistance_rate']
    )
    
    return HeterogeneousPatient(patient_id, baseline_va, characteristics)
```

### 3. Catastrophic Events

**Configuration Structure Reconciliation**:
```yaml
catastrophic_events:
  geographic_atrophy:
    probability_per_month: 0.001  # Monthly probability
    vision_impact:
      distribution: uniform
      min: -30  # Negative indicates vision loss
      max: -10
    permanent: true
    can_occur_multiple_times: false
    
  subretinal_fibrosis:
    probability_per_month: 0.0005
    vision_impact:
      distribution: normal
      mean: -20
      std: 5
    permanent: true
    max_va_reduction: 20  # Also caps max achievable VA
```

## Final Reconciled Structure

### Core Components

1. **Patient Characteristics** (stored per patient):
   - `trajectory_class`: str
   - `treatment_effect_multiplier`: float (from class + correlations)
   - `disease_progression_multiplier`: float (from class + correlations)
   - `max_achievable_va`: float
   - `resistance_rate`: float
   - `treatments_received`: int
   - `catastrophic_event_history`: List[Dict]

2. **Update Cycle**:
   - Apply treatment benefit (with multiplier and resistance)
   - Apply disease progression (with multiplier)
   - Check catastrophic events
   - Add measurement noise
   - Enforce bounds

3. **Validation Tracking**:
   - Track outcomes by trajectory class
   - Compare to Seven-UP targets
   - Report heterogeneity impact

This reconciliation ensures consistency across all planning documents and provides a clear implementation guide.