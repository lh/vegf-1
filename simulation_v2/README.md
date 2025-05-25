# Simulation V2 - Clean Architecture with TDD

## Overview

This is a ground-up rewrite of the AMD treatment simulation using Test-Driven Development (TDD) and clean architecture principles.

### Key Improvements

1. **FOV Internal Model**: Uses 4 disease states (NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE) internally
2. **TOM for Output**: Converts to simple 'inject'/'no_inject' for visualization
3. **No Fluid Detection**: Removed misleading proxy, uses proper disease states
4. **Dual Engines**: Both ABS and DES for comparison
5. **Clean Separation**: Domain logic separate from simulation engines

## Architecture

```
simulation_v2/
├── core/                  # Domain models (shared by both engines)
│   ├── disease_model.py   # FOV disease states and transitions
│   ├── patient.py         # Patient state tracking
│   ├── protocol.py        # Treatment protocols
│   └── discontinuation.py # Discontinuation logic
├── engines/               # Simulation implementations
│   ├── base.py           # Common interface
│   ├── abs_engine.py     # Agent-based simulation
│   └── des_engine.py     # Discrete event simulation
└── serialization/         # FOV → TOM conversion
    └── parquet_writer.py  # Serialization for output
```

## Development Approach (TDD)

1. **Write tests first** - See `tests/` directory
2. **Define interfaces** - What each component should do
3. **Implement minimally** - Just enough to pass tests
4. **Refactor** - Improve code while tests pass

## Running Tests

```bash
cd /Users/rose/Code/CC
pytest simulation_v2/tests/ -v
```

## Key Design Decisions

### 1. Disease States (FOV)
- Internal model uses full complexity
- Probabilistic transitions
- Treatment affects transition probabilities
- No fluid detection

### 2. Treatment Decision (TOM)
- Simplified to 'inject' or 'no_inject'
- Based on protocol + disease state
- What matters for visualization

### 3. Engine Comparison
- ABS: Models individual clinicians, patient agents
- DES: Event-driven, system-level view
- Same domain models, different execution

## Implementation Status

- [x] Test structure defined
- [x] Core domain tests written
- [x] Serialization tests written
- [x] Engine comparison tests written
- [ ] Domain models implemented
- [ ] Engines implemented
- [ ] Integration complete

## Next Steps

1. Implement domain models to pass tests
2. Build simulation engines
3. Create serialization layer
4. Integration testing
5. Performance comparison

## Migration from V1

### What Changes
- No more fluid detection
- Proper disease state usage
- Clean separation of concerns

### What Stays Same  
- Parquet output format (just 'inject'/'no_inject')
- Visualization compatibility
- Parameter structure (mostly)

## Questions/Decisions Needed

1. **Clinician modeling**: How much variation in ABS?
2. **Scheduling constraints**: How to model in DES?
3. **Parameter validation**: How strict?
4. **Performance targets**: How fast is fast enough?