# Clinical Improvements Integration Plan

## Overview
Integrate the clinical improvements module with the existing protocol manager and simulation runner infrastructure.

## Current Architecture

### 1. Protocol Flow
```
Protocol YAML → ProtocolSpecification → SimulationRunner → Engine (ABS/DES)
                     ↓
              Contains all parameters
              (no defaults allowed)
```

### 2. Key Components
- **ProtocolSpecification**: Immutable protocol definition (simulation_v2/protocols/protocol_spec.py)
- **SimulationRunner**: V2 engine wrapper (simulation_v2/core/simulation_runner.py)
- **APE SimulationRunner**: Streamlit bridge (ape/core/simulation_runner.py)
- **UI**: Protocol Manager (pages/1_Protocol_Manager.py) and Simulations (pages/2_Simulations.py)

## Integration Strategy

### Option 1: Protocol-Level Integration (Recommended) ✅
Add clinical improvements as optional protocol parameters that can be enabled/disabled.

**Advantages:**
- Improvements become part of the protocol specification
- Full traceability and audit trail
- Can save/load improvement settings with protocols
- UI can show toggle in Protocol Manager

**Implementation:**
1. Extend protocol YAML schema to include clinical improvements section
2. Modify ProtocolSpecification to handle optional improvements
3. Pass improvements config to simulation runner
4. Apply improvements in patient generation

### Option 2: Runtime Flag Integration
Add improvements as runtime parameters separate from protocol.

**Advantages:**
- No protocol changes needed
- Can A/B test same protocol with/without improvements

**Disadvantages:**
- Less traceable
- Settings not saved with protocol

## Detailed Implementation Plan

### Phase 1: Extend Protocol Schema

#### 1.1 Update Protocol YAML Format
```yaml
# Existing protocol fields...

# NEW: Clinical improvements section (optional)
clinical_improvements:
  enabled: true  # Master toggle
  
  # Individual feature flags
  use_loading_phase: true
  use_time_based_discontinuation: true
  use_response_based_vision: true
  use_baseline_distribution: true
  use_response_heterogeneity: true
  
  # Override default parameters (optional)
  loading_phase_parameters:
    loading_injections: 3
    loading_interval_days: 28
    
  discontinuation_parameters:
    annual_probabilities:
      1: 0.125
      2: 0.15
      3: 0.12
      4: 0.08
      5: 0.075
```

#### 1.2 Create Migration Script
```python
# simulation_v2/protocols/migrate_protocols.py
def add_clinical_improvements_section(protocol_path):
    """Add clinical improvements with defaults disabled to existing protocols"""
```

### Phase 2: Modify ProtocolSpecification

#### 2.1 Update ProtocolSpecification Class
```python
@dataclass(frozen=True)
class ProtocolSpecification:
    # ... existing fields ...
    
    # Optional clinical improvements
    clinical_improvements: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_yaml(cls, filepath: Path) -> 'ProtocolSpecification':
        # ... existing validation ...
        
        # Clinical improvements are optional
        clinical_improvements = data.get('clinical_improvements')
        if clinical_improvements:
            _validate_clinical_improvements(clinical_improvements)
```

### Phase 3: Integrate with SimulationRunner

#### 3.1 Modify V2 SimulationRunner
```python
class SimulationRunner:
    def __init__(self, protocol_spec: ProtocolSpecification):
        # ... existing init ...
        
        # Initialize clinical improvements if specified
        self.clinical_improvements = None
        if protocol_spec.clinical_improvements and protocol_spec.clinical_improvements.get('enabled'):
            from simulation_v2.clinical_improvements import ClinicalImprovements
            self.clinical_improvements = ClinicalImprovements.from_dict(
                protocol_spec.clinical_improvements
            )
            
    def _create_patients(self, n_patients: int, seed: int) -> List[Patient]:
        """Create patients with optional clinical improvements"""
        patients = []
        
        for i in range(n_patients):
            # Create base patient
            patient = self._create_base_patient(i)
            
            # Wrap with improvements if enabled
            if self.clinical_improvements:
                from simulation_v2.clinical_improvements import ImprovedPatientWrapper
                patient = ImprovedPatientWrapper(patient, self.clinical_improvements)
                
            patients.append(patient)
            
        return patients
```

### Phase 4: UI Integration

#### 4.1 Protocol Manager UI
Add toggle in Protocol Manager to enable/disable improvements:

```python
# In pages/1_Protocol_Manager.py
with st.expander("Clinical Improvements (Beta)", expanded=False):
    st.info("Enable realistic clinical patterns based on real-world data")
    
    # Master toggle
    improvements_enabled = st.checkbox(
        "Enable Clinical Improvements",
        value=protocol_data.get('clinical_improvements', {}).get('enabled', False),
        help="Apply loading phase, realistic discontinuation, and response heterogeneity"
    )
    
    if improvements_enabled:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Features")
            use_loading = st.checkbox("Loading Phase", value=True)
            use_discontinuation = st.checkbox("Time-based Discontinuation", value=True)
            use_response = st.checkbox("Response-based Vision", value=True)
            
        with col2:
            st.subheader("Heterogeneity")
            use_baseline_dist = st.checkbox("Baseline Distribution", value=True)
            use_response_types = st.checkbox("Response Types", value=True)
```

#### 4.2 Display Active Improvements
Show which improvements are active in the simulation page:

```python
# In pages/2_Simulations.py
if protocol_info['spec'].clinical_improvements and protocol_info['spec'].clinical_improvements.get('enabled'):
    with st.expander("Active Clinical Improvements", expanded=False):
        improvements = protocol_info['spec'].clinical_improvements
        active = [k.replace('use_', '').replace('_', ' ').title() 
                 for k, v in improvements.items() 
                 if k.startswith('use_') and v]
        st.write("- " + "\n- ".join(active))
```

### Phase 5: Testing & Validation

#### 5.1 Create Comparison Tests
```python
# simulation_v2/test_clinical_improvements_integration.py
def test_protocol_with_improvements():
    """Test that protocols correctly load and apply improvements"""
    
def test_backward_compatibility():
    """Test that old protocols without improvements still work"""
    
def test_side_by_side_comparison():
    """Run same protocol with and without improvements"""
```

#### 5.2 Add to CI/CD
- Add tests to ensure improvements don't break existing functionality
- Validate that results are deterministic with same seed

### Phase 6: Documentation

#### 6.1 Update Protocol Documentation
- Document new clinical_improvements section
- Provide examples of protocols with improvements
- Explain each improvement's effect

#### 6.2 Create Migration Guide
- How to update existing protocols
- Best practices for using improvements
- Interpreting results with improvements

## Implementation Timeline

1. **Week 1**: Protocol schema extension and migration
2. **Week 2**: ProtocolSpecification and SimulationRunner integration  
3. **Week 3**: UI integration and testing
4. **Week 4**: Documentation and validation

## Rollback Plan

If issues arise:
1. All improvements have an 'enabled' flag - can disable globally
2. Existing protocols without improvements section continue to work
3. Can remove clinical_improvements section from protocols
4. Code remains modular - easy to remove integration points

## Success Criteria

- [ ] Existing protocols work unchanged
- [ ] New protocols can enable improvements
- [ ] UI clearly shows improvement status
- [ ] Results are reproducible with same seed
- [ ] Performance impact < 10%
- [ ] Full audit trail of improvement settings