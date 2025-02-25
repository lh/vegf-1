# Agent-Based Simulation Improvement Plan

## Current State
- ABS has sophisticated patient modeling with detailed state tracking
- Fixed 8-injection schedule for the first year implemented
- HIGHLY_ACTIVE state handling improved and correctly reported
- Visualization is limited to basic timeline and acuity plots
- Patient data not aligned by treatment start
- No statistical analysis of outcomes

## Proposed Improvements

### 1. Patient Generation
- Add PatientGenerator to ABS (similar to DES)
- Implement Poisson process for realistic arrival patterns
- Configure arrival rate through YAML config
- Ensure proper initialization of agent states

### 2. Patient State Management
- Create dedicated AgentState class
- Track treatment timeline relative to start
- Store comprehensive visit history
- Maintain statistics for analysis
- Improve disease state transition logic and tracking

### 3. Clinical Outcomes
- Reuse ClinicalModel from DES
- Ensure consistent vision/OCT calculations
- Track treatment responses
- Monitor disease progression
- Refine HIGHLY_ACTIVE state occurrence and impact

### 4. Visualization and Analysis
- Use new OutcomeVisualizer
- Align timelines by treatment start
- Show mean acuity with confidence intervals
- Display patient retention rates
- Add statistical summaries

### 5. Configuration Updates
- Add ABS-specific parameters
- Configure patient generation
- Set clinic capacity
- Define outcome measures

## Implementation Steps

1. Patient Generation
```python
class ABSPatientGenerator:
    def __init__(self, rate_per_week, start_date, end_date, random_seed=None):
        # Similar to DES PatientGenerator
        pass
    
    def generate_arrival_times(self):
        # Return list of (time, patient_number) tuples
        pass
```

2. Agent State Management
```python
class AgentState:
    def __init__(self, patient_id, protocol, config):
        self.treatment_start = None
        self.visits = []
        self.outcomes = {}
        
    def record_visit(self, visit_data):
        # Track visit relative to treatment start
        pass
```

3. Clinical Model Integration
```python
class AgentBasedSimulation:
    def __init__(self, config, start_date):
        self.clinical_model = ClinicalModel()
        self.patient_generator = ABSPatientGenerator(...)
        
    def _simulate_vision_test(self, agent):
        return self.clinical_model.simulate_vision_change(agent.state)
```

4. Visualization Updates
```python
def run_test_simulation():
    # Create visualizer
    viz = OutcomeVisualizer()
    
    # Generate plots
    viz.plot_mean_acuity(patient_histories)
    viz.plot_patient_retention(patient_histories)
```

5. Configuration Example
```yaml
abs_parameters:
  patient_generation:
    rate_per_week: 3
    random_seed: 42
  clinic_capacity:
    daily_slots: 20
    days_per_week: 5
  outcome_measures:
    vision_improvement_threshold: 5
    treatment_success_threshold: 70
```

## Expected Benefits

1. More Realistic Simulation
- Natural patient flow
- Consistent clinical modeling
- Better state tracking

2. Better Analysis
- Proper timeline alignment
- Statistical rigor
- Confidence intervals

3. Improved Visualization
- Clear outcome trends
- Patient retention insights
- Treatment effectiveness measures

4. Enhanced Configurability
- Flexible patient generation
- Adjustable clinic parameters
- Customizable outcome measures

## Testing Strategy

1. Unit Tests
- Patient generation patterns
- State management
- Clinical calculations

2. Integration Tests
- End-to-end simulation runs
- Visualization accuracy
- Statistical validity

3. Validation Tests
- Compare with real-world data
- Verify clinical patterns
- Check resource utilization

## Next Steps

1. Refine existing modules:
   - simulation/abs.py: Optimize fixed injection schedule implementation
   - simulation/patient_state.py: Enhance disease state transition logic

2. Update test files:
   - test_abs_simulation.py: Add more comprehensive assertions for disease state transitions and HIGHLY_ACTIVE occurrences

3. Implement visualization improvements:
   - Use OutcomeVisualizer
   - Add ABS-specific plots, including disease state transition visualization

4. Enhance statistical analysis:
   - Implement analysis of HIGHLY_ACTIVE state occurrences and their impact on treatment outcomes

5. Documentation updates:
   - Update design_decisions.md to reflect the rationale behind the fixed injection schedule and HIGHLY_ACTIVE state handling

6. Create new modules (if not already done):
   - simulation/abs_patient_generator.py
   - simulation/agent_state.py

7. Add configuration (if not already done):
   - protocols/simulation_configs/abs_test.yaml

8. Write additional tests:
   - tests/unit/test_abs_generation.py
   - tests/unit/test_abs_outcomes.py
