# Migration Plan V2 - FOV Implementation & Fluid Detection Removal

**Created**: 2025-05-25  
**Approach**: Build new simulation from scratch with TDD

## Summary of Changes

### From Current State (V1)
- Mixed FOV/TOM usage
- Fluid detection determines disease state
- Enums in some paths, strings in others
- Business logic in UI layer

### To Target State (V2)
- FOV (4 states) internal only
- TOM ('inject'/'no_inject') for output only
- No fluid detection anywhere
- Clean separation of concerns

## Implementation Strategy

### Phase 1: Build Core with TDD (Week 1)
1. **Disease Model** ✓
   - DiseaseState enum (FOV)
   - Transition probabilities
   - No fluid detection

2. **Patient Model**
   - Track state, visits, treatment
   - Injection counting
   - Discontinuation handling

3. **Protocol Model**
   - Treatment decisions based on FOV
   - Discontinuation criteria
   - Monitoring schedules

### Phase 2: Build Engines (Week 2)
1. **Base Engine Interface**
   - Common API for both approaches
   - Shared domain models

2. **ABS Engine**
   - Individual patient agents
   - Clinician variation
   - Scheduling constraints

3. **DES Engine**
   - Event queue
   - System-level view
   - Deterministic scheduling

### Phase 3: Serialization Layer (Week 3)
1. **FOV → TOM Conversion**
   - At serialization boundary only
   - Simple inject/no_inject output

2. **Parquet Writer**
   - Standard schema
   - Compatible with existing viz

### Phase 4: Integration (Week 4)
1. **Streamlit Integration**
   - Replace simulation runner
   - Use new engines
   - Compare results side-by-side

2. **Migration of Existing Features**
   - Staggered enrollment
   - Parameter configurations
   - Visualization compatibility

## Key Technical Decisions

### 1. No Backward Compatibility Needed
- Fresh simulations only
- Old Parquet files can be deleted
- Focus on correctness over compatibility

### 2. Fluid Detection Removal
- Search and remove all references
- Replace with FOV state checks
- Update protocols accordingly

### 3. Engine Comparison
- Run both by default
- Statistical comparison tools
- Identify divergence patterns

## Testing Strategy

### Unit Tests (TDD)
- Each component tested in isolation
- Tests written before implementation
- Focus on behavior, not implementation

### Integration Tests
- Full simulation runs
- Parquet output validation
- Visualization compatibility

### Comparison Tests
- ABS vs DES consistency
- Statistical validation
- Performance benchmarks

## Migration Checkpoints

### Checkpoint 1: Core Complete
- [ ] All core tests pass
- [ ] No fluid detection in core
- [ ] FOV transitions working

### Checkpoint 2: Engines Running
- [ ] Both engines produce results
- [ ] Similar aggregate statistics
- [ ] Performance acceptable

### Checkpoint 3: Output Valid
- [ ] Parquet files created
- [ ] TOM format correct
- [ ] Visualizations work

### Checkpoint 4: Full Integration
- [ ] Streamlit updated
- [ ] Old code removed
- [ ] Documentation complete

## Risk Mitigation

1. **Parallel Development**: V2 doesn't touch V1 code
2. **Incremental Testing**: Each component validated
3. **Early Validation**: Core logic tested first
4. **Clear Boundaries**: FOV/TOM separation enforced

## Success Criteria

1. **No fluid detection** anywhere in code
2. **FOV states** used consistently internally
3. **TOM output** compatible with existing viz
4. **Both engines** produce valid results
5. **Clean architecture** with clear boundaries

## Next Actions

1. Run `python simulation_v2/run_tests.py` to see TDD in action
2. Implement Patient class to pass tests
3. Continue building incrementally
4. Remove fluid detection as we go