# Enum Inventory - Phase 0 Assessment

**Generated**: 2025-05-25  
**Purpose**: Document all enum types used in the codebase

## Enum Definitions

### 1. DiseaseState (simulation/clinical_model.py)
```python
class DiseaseState(Enum):
    NAIVE = 0
    STABLE = 1
    ACTIVE = 2
    HIGHLY_ACTIVE = 3
    
    def __str__(self):
        return self.name.lower()
```

**Purpose**: Represents AMD disease progression states  
**Values**: 
- NAIVE: Initial state, no prior treatment
- STABLE: Disease under control, minimal activity
- ACTIVE: Signs of activity, fluid accumulation
- HIGHLY_ACTIVE: High activity, significant fluid

**Special Notes**: 
- Has custom `__str__` method returning lowercase name
- This is the primary enum causing serialization issues

### 2. PhaseType (protocol_models.py)
```python
class PhaseType(Enum):
    LOADING = auto()
    MAINTENANCE = auto()
    EXTENSION = auto()
    DISCONTINUATION = auto()
    MONITORING = auto()
```

**Purpose**: Protocol phase types in treatment workflow  
**Usage**: Used in protocol definitions and phase transitions

### 3. ActionType (protocol_models.py)
```python
class ActionType(Enum):
    VISION_TEST = "vision_test"
    OCT_SCAN = "oct_scan" 
    INJECTION = "injection"
    CONSULTATION = "consultation"
```

**Purpose**: Clinical actions during visits  
**Values**: String-based enum values (not auto())

### 4. DecisionType (protocol_models.py)
```python
class DecisionType(Enum):
    NURSE_CHECK = "nurse_vision_check"
    DOCTOR_REVIEW = "doctor_treatment_decision"
    OCT_REVIEW = "doctor_oct_review"
```

**Purpose**: Types of clinical decision points  
**Values**: String-based enum values

### 5. ArchetypeBehavior (simulation/patient_state_archetype.py)
```python
class ArchetypeBehavior(Enum):
    # Need to check exact values
```

**Purpose**: Patient behavior archetypes
**Status**: Need to investigate usage

## Files Importing Enums

### Core simulation files:
- `simulation/clinical_model.py` - Defines DiseaseState
- `protocol_models.py` - Defines protocol-related enums
- `simulation/patient_state_archetype.py` - Defines ArchetypeBehavior
- `streamlit_app_parquet/simulation_runner.py` - Imports Enum for serialization fix

### Files potentially using enums:
- All simulation classes (ABS, DES variants)
- Patient state management
- Protocol implementations
- Visualization components

## Next Steps

1. Map which files use enums vs strings
2. Identify all serialization points
3. Document conversion patterns
4. Create test inventory