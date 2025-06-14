# Financial System V2 Modernization Implementation Plan

## Overview

This plan details the implementation of financial system modernization for simulation_v2, removing all backward compatibility with V1 and creating a native V2 financial system.

## Implementation Phases

### Phase 1: Core V2 Compatibility (Day 1)

#### 1.1 Update CostAnalyzer for V2 Data Formats

**File**: `simulation/economics/cost_analyzer.py`

**Changes**:
```python
# Update analyze_visit method to use V2 field names
def analyze_visit(self, visit: Dict[str, Any]) -> CostEvent:
    # Change from visit['time'] to visit['date']
    visit_date = visit['date']
    
    # Handle V2 disease state enums
    disease_state = visit.get('disease_state')
    if hasattr(disease_state, 'name'):
        disease_state_str = disease_state.name.lower()
    else:
        disease_state_str = str(disease_state).lower()
```

**Tasks**:
- [ ] Update all references from 'time' to 'date'
- [ ] Add enum handling for disease_state
- [ ] Update type hints to include V2 types
- [ ] Test with V2 visit data

#### 1.2 Create V2-Native Financial Results

**File**: `simulation_v2/economics/financial_results.py` (NEW)

**Implementation**:
```python
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any

@dataclass
class PatientCostSummary:
    """Cost summary for individual patient."""
    patient_id: str
    total_cost: float
    visit_costs: List[float]
    drug_costs: float
    monitoring_costs: float
    injection_count: int

@dataclass
class FinancialResults:
    """Financial analysis results for V2 simulations."""
    total_cost: float
    cost_per_patient: float
    cost_by_category: Dict[str, float]
    cost_by_phase: Dict[str, float]
    cost_per_injection: float
    cost_per_letter_gained: Optional[float]
    patient_costs: Dict[str, PatientCostSummary]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
```

**Tasks**:
- [ ] Create financial_results.py with dataclasses
- [ ] Add comprehensive type hints
- [ ] Include serialization methods
- [ ] Add validation methods

#### 1.3 Update CostTracker for V2 Patient Objects

**File**: `simulation/economics/cost_tracker.py`

**Changes**:
```python
def process_v2_results(self, results: 'SimulationResults') -> None:
    """Process V2 simulation results directly."""
    for patient_id, patient in results.patient_histories.items():
        # Work directly with Patient objects
        patient_events = []
        for visit in patient.visit_history:
            event = self.analyzer.analyze_visit(visit)
            patient_events.append(event)
        self.events[patient_id] = patient_events
```

**Tasks**:
- [ ] Add process_v2_results method
- [ ] Update to work with Patient objects directly
- [ ] Remove dictionary-based assumptions
- [ ] Add V2-specific type hints

### Phase 2: Native V2 Integration (Day 2)

#### 2.1 Implement Option A - Extend V2 Patient Class

**File**: `simulation_v2/core/patient.py`

**Changes**:
```python
from typing import Optional, Callable

class Patient:
    def __init__(self, patient_id: str, baseline_vision: int = 70,
                 visit_metadata_enhancer: Optional[Callable] = None):
        # ... existing init code ...
        self.visit_metadata_enhancer = visit_metadata_enhancer
    
    def record_visit(self, date: datetime, disease_state: DiseaseState,
                    treatment_given: bool, vision: int) -> None:
        """Record a patient visit with optional metadata enhancement."""
        visit = {
            'date': date,
            'disease_state': disease_state,
            'treatment_given': treatment_given,
            'vision': vision
        }
        
        # Apply metadata enhancement if configured
        if self.visit_metadata_enhancer:
            visit = self.visit_metadata_enhancer(visit, self)
        
        self.visit_history.append(visit)
        
        # ... rest of existing method ...
```

**Tasks**:
- [ ] Add visit_metadata_enhancer parameter to __init__
- [ ] Modify record_visit to apply enhancement
- [ ] Update docstrings
- [ ] Test with and without enhancer

#### 2.2 Create V2-Native Cost Metadata Enhancer

**File**: `simulation_v2/economics/cost_enhancer.py` (NEW)

**Implementation**:
```python
def create_v2_cost_enhancer(cost_config: Optional['CostConfig'] = None) -> Callable:
    """Create a cost metadata enhancer for V2 simulations."""
    
    def enhance_visit(visit: Dict[str, Any], patient: 'Patient') -> Dict[str, Any]:
        """Enhance visit with cost metadata."""
        # Initialize metadata
        metadata = visit.setdefault('metadata', {})
        
        # Determine phase
        visit_number = len(patient.visit_history) + 1
        metadata['phase'] = 'loading' if visit_number <= 3 else 'maintenance'
        
        # Add cost components
        components = ['vision_test', 'oct_scan']
        if visit.get('treatment_given'):
            components.append('injection')
        metadata['components_performed'] = components
        
        # Add drug info
        if visit.get('treatment_given'):
            metadata['drug'] = 'eylea_2mg'  # Default, can be configured
        
        # Add visit subtype
        metadata['visit_subtype'] = f"{metadata['phase']}_regular_visit"
        
        return visit
    
    return enhance_visit
```

**Tasks**:
- [ ] Move V2 enhancer to simulation_v2/economics
- [ ] Remove V1 compatibility code
- [ ] Add configuration support
- [ ] Add comprehensive tests

#### 2.3 Update Engine Integration

**File**: `simulation_v2/engines/abs_engine.py` and `des_engine.py`

**Changes**:
```python
class ABSEngine:
    def __init__(self, disease_model: DiseaseModel, protocol: Protocol,
                 n_patients: int, seed: Optional[int] = None,
                 visit_metadata_enhancer: Optional[Callable] = None):
        # ... existing init ...
        self.visit_metadata_enhancer = visit_metadata_enhancer
        
        # Apply to all patients if provided
        if self.visit_metadata_enhancer:
            for patient in self.patients.values():
                patient.visit_metadata_enhancer = self.visit_metadata_enhancer
```

**Tasks**:
- [ ] Add enhancer parameter to engine constructors
- [ ] Apply enhancer to all patients on initialization
- [ ] Update engine documentation
- [ ] Test with cost enhancer

### Phase 3: Clean Integration API (Day 3)

#### 3.1 Create Economics Integration Module

**File**: `simulation_v2/economics/integration.py` (NEW)

**Implementation**:
```python
from typing import Union, Optional
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.engines import ABSEngine, DESEngine
from .cost_enhancer import create_v2_cost_enhancer
from .financial_results import FinancialResults

class EconomicsIntegration:
    """Simple API for adding economics to V2 simulations."""
    
    @staticmethod
    def create_enhanced_engine(
        engine_type: str,
        protocol_spec: 'ProtocolSpecification',
        cost_config: 'CostConfig',
        n_patients: int,
        seed: Optional[int] = None,
        **kwargs
    ) -> Union[ABSEngine, DESEngine]:
        """Create a simulation engine with integrated cost tracking."""
        # Create disease model
        disease_model = DiseaseModel(
            transition_probabilities=protocol_spec.disease_transitions,
            treatment_effect_multipliers=protocol_spec.treatment_effect_on_transitions,
            seed=seed
        )
        
        # Create protocol
        protocol = StandardProtocol(
            min_interval_days=protocol_spec.min_interval_days,
            max_interval_days=protocol_spec.max_interval_days,
            extension_days=protocol_spec.extension_days,
            shortening_days=protocol_spec.shortening_days
        )
        
        # Create cost enhancer
        enhancer = create_v2_cost_enhancer(cost_config)
        
        # Create appropriate engine
        if engine_type.lower() == 'abs':
            return ABSEngine(
                disease_model=disease_model,
                protocol=protocol,
                n_patients=n_patients,
                seed=seed,
                visit_metadata_enhancer=enhancer,
                **kwargs
            )
        else:
            return DESEngine(
                disease_model=disease_model,
                protocol=protocol,
                n_patients=n_patients,
                seed=seed,
                visit_metadata_enhancer=enhancer,
                **kwargs
            )
    
    @staticmethod
    def analyze_results(
        results: 'SimulationResults',
        cost_config: 'CostConfig'
    ) -> FinancialResults:
        """Analyze financial outcomes from simulation results."""
        from simulation.economics import CostAnalyzer, CostTracker
        
        analyzer = CostAnalyzer(cost_config)
        tracker = CostTracker(analyzer)
        
        # Process V2 results directly
        tracker.process_v2_results(results)
        
        # Calculate financial metrics
        summary = tracker.get_summary_statistics()
        
        # Calculate cost per letter gained
        cost_per_letter = None
        if hasattr(results, 'va_change') and results.va_change > 0:
            cost_per_letter = summary['avg_cost_per_patient'] / results.va_change
        
        return FinancialResults(
            total_cost=summary['total_cost'],
            cost_per_patient=summary['avg_cost_per_patient'],
            cost_by_category=summary.get('cost_by_category', {}),
            cost_by_phase=summary.get('cost_by_phase', {}),
            cost_per_injection=summary.get('cost_per_injection', 0),
            cost_per_letter_gained=cost_per_letter,
            patient_costs=tracker.get_patient_summaries()
        )
```

**Tasks**:
- [ ] Create integration module
- [ ] Implement factory methods
- [ ] Add comprehensive documentation
- [ ] Create usage examples

#### 3.2 Create Simplified Run Script

**File**: `run_v2_simulation_with_economics.py` (NEW)

**Implementation**:
```python
#!/usr/bin/env python3
"""Run V2 simulation with integrated economics - simplified API."""

from pathlib import Path
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.economics import EconomicsIntegration, CostConfig

def main():
    # Load configurations
    protocol = ProtocolSpecification.from_yaml("protocols/eylea.yaml")
    cost_config = CostConfig.from_yaml("configs/nhs_standard.yaml")
    
    # Create enhanced engine - one line!
    engine = EconomicsIntegration.create_enhanced_engine(
        'abs', protocol, cost_config, n_patients=100, seed=42
    )
    
    # Run simulation
    results = engine.run(duration_years=2.0)
    
    # Analyze costs - one line!
    financial = EconomicsIntegration.analyze_results(results, cost_config)
    
    # Display results
    print(f"Clinical: {results.mean_va_change:.1f} letters")
    print(f"Financial: £{financial.cost_per_patient:,.2f} per patient")
    print(f"Cost-effectiveness: £{financial.cost_per_letter_gained:,.2f} per letter")

if __name__ == "__main__":
    main()
```

**Tasks**:
- [ ] Create simplified run script
- [ ] Test end-to-end integration
- [ ] Add error handling
- [ ] Create output formatting

### Phase 4: Cleanup and Migration (Day 4)

#### 4.1 Remove V1 Compatibility Code

**Files to Update**:
- `simulation/economics/cost_metadata_enhancer.py` - Remove or deprecate
- `simulation/economics/simulation_adapter.py` - Remove V1 methods
- `simulation/economics/visit_enhancer.py` - Remove if redundant

**Tasks**:
- [ ] Remove old cost_metadata_enhancer.py
- [ ] Remove dictionary conversion code
- [ ] Remove field name mappings (time->date)
- [ ] Update imports throughout codebase

#### 4.2 Update Existing Scripts

**Files to Update**:
- `run_v2_simulation_with_costs.py` - Simplify using new API
- `run_v2_simulation_with_costs_integrated.py` - Deprecate

**Tasks**:
- [ ] Update scripts to use new integration API
- [ ] Remove manual data conversion code
- [ ] Simplify to use clean API
- [ ] Add deprecation notices

#### 4.3 Add Type Hints Throughout

**All economics files**:
```python
from typing import Protocol

class CostAnalyzable(Protocol):
    """Protocol for objects that can be analyzed for costs."""
    visit_history: List[VisitRecord]
    baseline_vision: int
    id: str
```

**Tasks**:
- [ ] Add type stubs for V2 objects
- [ ] Create protocol definitions
- [ ] Update all function signatures
- [ ] Run mypy for validation

### Phase 5: Testing and Documentation (Day 5)

#### 5.1 Create V2-Specific Tests

**File**: `tests/test_v2_economics_integration.py` (NEW)

**Test Coverage**:
```python
def test_engine_creation_with_economics():
    """Test creating engines with cost tracking."""
    
def test_cost_enhancement():
    """Test visit enhancement with cost metadata."""
    
def test_financial_analysis():
    """Test end-to-end financial analysis."""
    
def test_cost_per_letter_calculation():
    """Test cost-effectiveness metrics."""
```

**Tasks**:
- [ ] Create comprehensive test suite
- [ ] Test engine creation
- [ ] Test visit enhancement
- [ ] Test financial calculations
- [ ] Test edge cases

#### 5.2 Update Documentation

**Files**:
- `README.md` - Add V2 economics section
- `docs/economics_guide.md` - Create usage guide
- `CHANGELOG.md` - Document changes

**Tasks**:
- [ ] Write usage guide
- [ ] Add API documentation
- [ ] Create migration guide
- [ ] Update examples

## Success Criteria

1. **No Data Conversion**: V2 simulations work with economics without any manual data conversion
2. **Clean API**: Economics can be added to any V2 simulation with 1-2 lines of code
3. **Type Safety**: All economics code has proper type hints and passes mypy
4. **Performance**: No noticeable performance impact from cost tracking
5. **Tests Pass**: All existing tests pass, new tests provide >90% coverage

## Risk Mitigation

1. **Backward Compatibility**: Keep old files during transition, mark as deprecated
2. **Testing**: Extensive testing at each phase before moving forward
3. **Rollback Plan**: Git branches for each phase allow easy rollback
4. **Incremental Delivery**: Each phase delivers working functionality

## Timeline Summary

- **Day 1**: Core V2 compatibility (analyzer, results, tracker)
- **Day 2**: Native integration (Patient enhancement, V2 enhancer, engines)
- **Day 3**: Clean API (integration module, simplified scripts)
- **Day 4**: Cleanup and migration
- **Day 5**: Testing and documentation

Total: 5 working days for complete V2 modernization