# V2 Architecture and Development Plans

## Overview

The V2 simulation system is a complete rewrite focusing on scientific rigor, parameter traceability, and clean architecture. This document captures the design decisions, implementation details, and future plans.

## Core Principles

### 1. **No Hidden Parameters**
- Every parameter must be explicitly defined in protocol files
- No hardcoded defaults in the codebase
- Missing parameters cause immediate failure
- Complete parameter lineage from source to result

### 2. **Scientific Integrity**
- No synthetic or fallback data
- Fail fast on missing or invalid inputs
- Full reproducibility through checksums and seeds
- Audit trail for every simulation run

### 3. **Clean Architecture**
- Complete separation from V1 codebase
- Test-Driven Development (TDD)
- Strong typing throughout
- Immutable protocol specifications

## Architecture Components

### Simulation Engine (`simulation_v2/`)

```
simulation_v2/
├── core/
│   ├── disease_model.py      # FOV disease state transitions
│   ├── patient.py            # Patient state tracking
│   ├── protocol.py           # Treatment protocol interface
│   └── simulation_runner.py  # Main simulation orchestrator
├── engines/
│   ├── abs_engine.py         # Agent-based simulation
│   └── des_engine.py         # Discrete event simulation
├── protocols/
│   └── protocol_spec.py      # Protocol specification system
├── serialization/
│   └── parquet_writer.py     # FOV→TOM conversion
└── tests/                    # Comprehensive test suite
```

### Key Design Decisions

1. **FOV (Four Option Version) Internal Model**
   - States: NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE
   - Based on clinical understanding of disease progression
   - No "fluid detection" proxy

2. **TOM (Two Option Model) Output**
   - Simple inject/no_inject for visualization
   - Clean separation of internal model from output format
   - Enables easier analysis and comparison

3. **Days as Base Time Unit**
   - All internal calculations use days
   - Eliminates precision loss from unit conversions
   - Direct compatibility with datetime operations
   - Convenience methods for weeks/months where needed

4. **Protocol Specification System**
   - YAML-based protocol definitions
   - SHA-256 checksums for version tracking
   - Immutable specifications after loading
   - Complete validation at load time

## Protocol Structure

### Required Sections

1. **Metadata**
   ```yaml
   name: "Protocol Name"
   version: "1.0"
   author: "Author Name"
   description: "Detailed description"
   ```

2. **Treatment Parameters**
   ```yaml
   protocol_type: "treat_and_extend"
   min_interval_days: 28
   max_interval_days: 112
   extension_days: 14
   shortening_days: 14
   ```

3. **Disease Model**
   - Transition probabilities (must sum to 1.0)
   - Treatment effect multipliers
   - Vision change parameters for all scenarios

4. **Population Parameters**
   - Baseline vision distribution
   - Inclusion/exclusion criteria

5. **Discontinuation Rules**
   - Poor vision thresholds
   - High injection burden
   - Long treatment duration

## Streamlit V2 Interface

### Pages

1. **Protocol Manager**
   - Browse and validate protocols
   - View all parameters with explanations
   - Export in multiple formats
   - Checksum verification

2. **Run Simulation**
   - Engine selection (ABS/DES)
   - Parameter configuration
   - Progress tracking
   - Immediate results summary

3. **Analysis Overview**
   - Vision outcome distributions
   - Treatment patterns
   - Patient trajectories
   - Audit trail viewer

### Session State Management
- Current protocol specification
- Simulation results
- Audit trail
- No hidden state or defaults

## Future Development Plans

### Phase 1: Core Enhancements (Current)
- [x] Protocol specification system
- [x] Basic Streamlit interface
- [x] Audit trail implementation
- [ ] Protocol comparison tools
- [ ] Batch simulation runner

### Phase 2: Advanced Features
- [ ] **Loading Phase Implementation**
  - Initial monthly injections before T&E
  - Configurable loading duration
  - Different criteria for entering T&E

- [ ] **Retreatment Logic**
  - Criteria for stopping treatment
  - Monitoring phase behavior
  - Retreatment triggers
  - Track retreatment cycles

- [ ] **Complex Protocols**
  - PRN (as-needed) protocols
  - Hybrid protocols (T&E + PRN)
  - Protocol switching logic

### Phase 3: Analysis Tools
- [ ] **Statistical Framework**
  - Hypothesis testing between protocols
  - Confidence intervals
  - Power calculations
  - Non-inferiority testing

- [ ] **Visualization Suite**
  - Streamgraph for patient states
  - Sankey diagrams for transitions
  - Survival curves
  - Cost-effectiveness plots

- [ ] **Validation Tools**
  - Compare to clinical trial data
  - Parameter calibration
  - Sensitivity analysis
  - Monte Carlo uncertainty

### Phase 4: Production Features
- [ ] **Performance Optimization**
  - Parallel simulation runs
  - Results caching
  - Incremental computation
  - Cloud deployment ready

- [ ] **Collaboration Features**
  - Protocol sharing
  - Results comparison
  - Annotation system
  - Version control integration

## Technical Debt and Considerations

### Current Limitations
1. Vision model is simplified (Gaussian changes)
2. No OCT or biomarker modeling yet
3. Single eye simulation only
4. No resource constraints modeling

### Future Improvements
1. Realistic vision trajectories
2. Bilateral eye coordination
3. Clinic capacity constraints
4. Cost modeling

## Migration from V1

### Key Differences
1. **Parameters**: V1 has defaults, V2 requires explicit definition
2. **Disease Model**: V1 uses fluid detection, V2 uses FOV states
3. **Output**: V1 mixes concerns, V2 separates FOV/TOM
4. **Architecture**: V1 evolved organically, V2 designed upfront

### Migration Strategy
1. Run V1 and V2 in parallel for validation
2. Port visualization code to V2 gradually
3. Maintain separate codebases during transition
4. Document parameter mappings

## Testing Strategy

### Unit Tests
- All core components have tests
- Disease state transitions
- Patient state management
- Protocol decisions
- Serialization logic

### Integration Tests
- Engine comparison (ABS vs DES)
- Protocol loading and validation
- End-to-end simulation runs
- Audit trail completeness

### Validation Tests
- Statistical properties
- Conservation laws (patient counts)
- Parameter bounds
- Reproducibility with seeds

## Documentation Standards

### Code Documentation
- Docstrings for all public methods
- Type hints throughout
- Usage examples in docstrings
- NO TODOs in production code

### Protocol Documentation
- Purpose and rationale
- Parameter justification
- Literature references
- Validation status

### User Documentation
- Quick start guides
- Protocol authoring guide
- Analysis tutorials
- Troubleshooting guide

## Performance Considerations

### Current Performance
- 100 patients × 2 years: ~0.1 seconds
- 1000 patients × 5 years: ~2 seconds
- Linear scaling with patient count

### Optimization Opportunities
1. Vectorize patient operations
2. Cython for hot loops
3. Parallel patient processing
4. GPU acceleration for large scales

## Security and Compliance

### Data Security
- No PHI in simulation
- Synthetic patients only
- Audit trails are anonymous
- No network dependencies

### Reproducibility
- Git hash in audit trail
- Protocol checksums
- Random seed tracking
- Environment versioning

## Conclusion

The V2 system represents a ground-up redesign focusing on scientific rigor and reproducibility. By eliminating all hidden parameters and defaults, we ensure complete traceability from protocol definition to simulation results. The clean architecture enables easy extension while maintaining the integrity of the core simulation engine.

### Success Metrics
1. Zero hardcoded parameters
2. 100% reproducible results
3. Complete audit trails
4. Fast simulation execution
5. Intuitive user interface

### Next Immediate Steps
1. Add protocol comparison visualization
2. Implement batch simulation runner
3. Create protocol template library
4. Add statistical analysis tools
5. Write user documentation