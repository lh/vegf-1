# Enum Serialization Migration Plan

**Created**: 2025-05-25  
**Status**: Phase 0 - Assessment  
**Target**: Consistent enum usage with proper serialization boundaries

## Executive Summary

The codebase currently has inconsistent handling of enum types (particularly `DiseaseState`). Some code paths use enums internally and convert to strings, others use strings directly. This causes serialization errors when saving to Parquet and makes the code fragile and hard to maintain.

This migration will establish enums as the internal representation with explicit serialization at storage boundaries.

## Current Problems

1. **Inconsistent representations**: 
   - `TreatAndExtendABS` uses `DiseaseState` enums
   - `treat_and_extend_abs_fixed.py` uses string literals ('active', 'stable')
   - Staggered simulations inherit enum usage
   - DES variants use strings directly

2. **Serialization failures**: 
   - Parquet cannot serialize Python enums
   - Ad-hoc conversions added as band-aids
   - Different code paths handle this differently

3. **Type safety issues**:
   - No guarantee of valid values with strings
   - Potential for typos and case mismatches
   - Lost IDE support and refactoring capability

## Migration Phases

### Phase 0: Assessment and Mothballing (Current)
- Document all enum usage
- Map serialization points
- Archive non-Parquet version
- Establish testing baseline

### Phase 1: Create Serialization Infrastructure
- Build `SimulationSerializer` class
- Define serialization contracts
- Create comprehensive test suite
- Document serialization patterns

### Phase 2: Fix Data Generation
- Remove string literals from simulations
- Use enums consistently in all variants
- Add serialization at save points
- Test each simulation type

### Phase 3: Fix Data Loading  
- Add deserialization for Parquet loading
- Update all data consumers
- Ensure backward compatibility
- Handle legacy data files

### Phase 4: Validation and Cleanup
- End-to-end testing
- Remove temporary workarounds
- Update documentation
- Performance validation

## Design Principles

1. **Enums for internal use**: Type safety and IDE support within simulation
2. **Strings for storage**: Portability and tool compatibility in files
3. **Explicit boundaries**: Clear serialization/deserialization points
4. **Backward compatibility**: Must handle existing Parquet files
5. **Single source of truth**: One place defines each enum

## Technical Approach

### Serialization Layer
```python
# simulation/serialization.py
class SimulationSerializer:
    """Central point for all enum↔string conversions"""
    
    @staticmethod
    def serialize_value(value: Any) -> Any:
        """Convert enums to strings, pass through everything else"""
        if isinstance(value, Enum):
            return value.name
        return value
```

### Usage Pattern
```python
# Before saving to Parquet
serialized_data = SimulationSerializer.serialize_dict(visit_data)

# After loading from Parquet  
domain_data = SimulationSerializer.deserialize_visit(parquet_data)
```

## Success Criteria

1. All simulations use enums internally
2. All Parquet files store strings
3. No ad-hoc enum detection code
4. Existing Parquet files still load correctly
5. Type hints accurate throughout
6. No regression in functionality

## Risk Mitigation

1. **Comprehensive testing**: Snapshot tests before any changes
2. **Gradual rollout**: One simulation type at a time
3. **Backward compatibility**: Always test with old files
4. **Rollback plan**: Each phase independently revertable
5. **Documentation**: Clear migration guide for developers

## Timeline Estimate

- Phase 0: 2-3 days
- Phase 1: 3-4 days  
- Phase 2: 1 week
- Phase 3: 1 week
- Phase 4: 2-3 days

Total: ~3-4 weeks with testing

## Next Steps

1. Complete Phase 0 assessment
2. Review findings and adjust plan
3. Get stakeholder buy-in
4. Begin Phase 1 implementation