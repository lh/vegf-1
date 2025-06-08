# Financial System V2 Modernization Report

## Executive Summary

The current financial system was designed for the original simulation infrastructure and requires several adaptations to work with simulation_v2. This report outlines recommended changes to fully modernize the financial system for V2, removing all backward compatibility requirements.

## Current Integration Challenges

### 1. Data Format Mismatches

**Issue**: The financial system expects visit records with specific field names that differ from V2:
- V2 uses `date` while the financial system expects `time`
- V2 stores enums directly while the financial system expects string representations
- V2 uses `Patient.visit_history` while the financial system expects a `visits` key in patient data

**Current Workaround**: Manual conversion in `run_v2_simulation_with_costs_integrated.py` (lines 90-132)

### 2. Patient Model Differences

**Issue**: The cost metadata enhancer was designed for the old `PatientState` class:
- References `patient_state.state.get('current_phase')` which doesn't exist in V2
- Expects different patient attributes and methods

**Current Workaround**: Created `cost_metadata_enhancer_v2.py` as a separate implementation

### 3. Architectural Misalignment

**Issue**: The financial system assumes a different simulation architecture:
- Expects simulation results as dictionaries with specific structure
- Designed around the old simulation's data flow
- Cost adapter expects pre-processed patient histories

**Current Workaround**: Wrapper code to reshape V2 data before passing to financial components

## Recommended Modernization Changes

### 1. Native V2 Data Format Support

**Change**: Update all financial components to work directly with V2 data structures.

#### cost_analyzer.py
```python
# Current
def analyze_visit(self, visit: Dict[str, Any]) -> CostEvent:
    time = visit['time']  # Expects 'time'
    
# Recommended
def analyze_visit(self, visit: Dict[str, Any]) -> CostEvent:
    visit_date = visit['date']  # Use V2's 'date' field
    
    # Handle V2 enums directly
    if hasattr(visit.get('disease_state'), 'name'):
        disease_state = visit['disease_state'].name
    else:
        disease_state = visit.get('disease_state')
```

#### simulation_adapter.py
```python
# Current: Expects dictionary-based patient histories
def process_simulation_results(self, simulation_results: Dict[str, Any])

# Recommended: Accept V2 SimulationResults directly
def process_simulation_results(self, results: 'SimulationResults') -> FinancialResults:
    """Process V2 simulation results directly."""
    for patient_id, patient in results.patient_histories.items():
        # Work directly with Patient objects
        costs = self.analyze_patient(patient)
```

### 2. Unified Metadata Enhancement

**Change**: Merge the metadata enhancement directly into V2's visit recording process.

#### Option A: Extend V2 Patient Class
```python
# In simulation_v2/core/patient.py
class Patient:
    def __init__(self, patient_id: str, baseline_vision: int = 70, 
                 cost_metadata_enhancer: Optional[Callable] = None):
        # ... existing init ...
        self.cost_metadata_enhancer = cost_metadata_enhancer
    
    def record_visit(self, date: datetime, disease_state: DiseaseState,
                    treatment_given: bool, vision: int) -> None:
        visit = {
            'date': date,
            'disease_state': disease_state,
            'treatment_given': treatment_given,
            'vision': vision
        }
        
        # Apply cost metadata enhancement if configured
        if self.cost_metadata_enhancer:
            visit = self.cost_metadata_enhancer(visit, self)
        
        self.visit_history.append(visit)
```

#### Option B: Visit Factory Pattern
```python
# New file: simulation_v2/core/visit_factory.py
class VisitFactory:
    """Factory for creating visit records with optional enhancements."""
    
    def __init__(self, enhancers: List[VisitEnhancer] = None):
        self.enhancers = enhancers or []
    
    def create_visit(self, date: datetime, patient: Patient, 
                    disease_state: DiseaseState, treatment_given: bool,
                    vision: int) -> Dict[str, Any]:
        visit = {
            'date': date,
            'disease_state': disease_state,
            'treatment_given': treatment_given,
            'vision': vision
        }
        
        for enhancer in self.enhancers:
            visit = enhancer.enhance(visit, patient)
        
        return visit
```

### 3. V2-Native Financial Components

**Change**: Create new financial components designed specifically for V2.

#### New Structure:
```
simulation_v2/
├── economics/
│   ├── __init__.py
│   ├── cost_config.py          # Keep as-is (YAML-based config)
│   ├── cost_analyzer.py        # V2-native analyzer
│   ├── cost_tracker.py         # V2-native tracker
│   ├── financial_results.py    # New results class
│   └── visit_enhancer.py       # V2 visit enhancement
```

#### financial_results.py
```python
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

### 4. Simplified Integration API

**Change**: Create a clean API for adding financial analysis to V2 simulations.

```python
# simulation_v2/economics/integration.py
class EconomicsIntegration:
    """Simple API for adding economics to V2 simulations."""
    
    @staticmethod
    def create_enhanced_engine(engine_type: str, protocol_spec: ProtocolSpecification,
                              cost_config: CostConfig, **kwargs) -> Union[ABSEngine, DESEngine]:
        """Create a simulation engine with integrated cost tracking."""
        # Create base components
        disease_model = DiseaseModel.from_protocol(protocol_spec)
        protocol = StandardProtocol.from_protocol(protocol_spec)
        
        # Create cost enhancer
        enhancer = CostVisitEnhancer(cost_config)
        
        # Create engine with enhancement
        if engine_type == 'abs':
            return ABSEngineWithCosts(disease_model, protocol, 
                                     visit_enhancer=enhancer, **kwargs)
        else:
            return DESEngineWithCosts(disease_model, protocol,
                                     visit_enhancer=enhancer, **kwargs)
    
    @staticmethod
    def analyze_results(results: SimulationResults, cost_config: CostConfig) -> FinancialResults:
        """Analyze financial outcomes from simulation results."""
        analyzer = CostAnalyzer(cost_config)
        return analyzer.analyze_simulation(results)
```

### 5. Remove Legacy Dependencies

**Change**: Eliminate all code that exists solely for V1 compatibility.

**Files to refactor/remove**:
- `simulation/economics/cost_metadata_enhancer.py` → Merge into V2 enhancer
- `simulation/economics/simulation_adapter.py` → Replace with V2-native version
- `simulation/economics/visit_enhancer.py` → Redesign for V2

**Fields/patterns to remove**:
- References to `patient_state.state`
- Conversion between `time` and `date`
- Dictionary-based patient history assumptions
- String-based disease state handling

### 6. Type Safety Improvements

**Change**: Add proper type hints throughout the financial system.

```python
from typing import Protocol, TypedDict

class VisitRecord(TypedDict):
    """Type definition for V2 visit records."""
    date: datetime
    disease_state: DiseaseState
    treatment_given: bool
    vision: int
    metadata: Dict[str, Any]

class CostAnalyzable(Protocol):
    """Protocol for objects that can be analyzed for costs."""
    visit_history: List[VisitRecord]
    baseline_vision: int
    patient_id: str
```

## Implementation Priority

### Phase 1: Core Compatibility (1-2 days)
1. Update `cost_analyzer.py` to handle V2 data formats natively
2. Create `financial_results.py` with proper V2 result classes
3. Update `cost_tracker.py` to work with V2 Patient objects

### Phase 2: Clean Integration (2-3 days)
1. Implement the `EconomicsIntegration` API
2. Create V2-native visit enhancement system
3. Update engines to support visit enhancement natively

### Phase 3: Cleanup (1 day)
1. Remove all V1 compatibility code
2. Consolidate metadata enhancers into single V2 implementation
3. Add comprehensive type hints

### Phase 4: Testing & Documentation (1-2 days)
1. Create V2-specific financial tests
2. Update documentation for V2 usage
3. Create migration guide for existing code

## Benefits of Modernization

1. **Simpler Integration**: No need for data conversion or wrapper code
2. **Better Performance**: Direct access to V2 data structures
3. **Type Safety**: Proper typing reduces runtime errors
4. **Maintainability**: Single codebase without compatibility layers
5. **Extensibility**: Clean architecture for future enhancements

## Example Usage After Modernization

```python
from simulation_v2.economics import EconomicsIntegration, CostConfig

# Simple, clean integration
cost_config = CostConfig.from_yaml("configs/nhs_standard.yaml")
protocol = ProtocolSpecification.from_yaml("protocols/eylea.yaml")

# Create enhanced engine in one line
engine = EconomicsIntegration.create_enhanced_engine(
    'abs', protocol, cost_config, n_patients=100, seed=42
)

# Run simulation
results = engine.run(duration_years=2.0)

# Analyze costs directly
financial_results = EconomicsIntegration.analyze_results(results, cost_config)

print(f"Cost per patient: £{financial_results.cost_per_patient:,.2f}")
print(f"Cost per letter gained: £{financial_results.cost_per_letter_gained:,.2f}")
```

## Conclusion

The recommended changes will create a financial system that is:
- Native to V2's architecture
- Simpler to use and maintain
- More performant
- Type-safe and modern

By removing backward compatibility requirements, we can create a cleaner, more maintainable system that fully leverages V2's improved architecture.