# Memory-Aware Architecture Implementation Plan

## Overview

This plan outlines the implementation of a memory-aware architecture for APE V2, enabling deployment on Streamlit Cloud free tier (1GB RAM) while supporting simulations of 100K+ patients.

## Implementation Phases

### Phase 1: Foundation (Day 1-2)
**Goal**: Establish core infrastructure without breaking existing functionality

1. **Two-Tier Results System**
   - Create abstract `SimulationResults` base class
   - Implement `InMemoryResults` for small simulations
   - Implement `ParquetResults` for large simulations
   - Factory method for automatic selection

2. **Basic Memory Monitoring**
   - Add psutil dependency
   - Create memory monitoring utility
   - Add warnings at 70% threshold
   - Display current usage in sidebar

3. **Regression Test Suite**
   - Test existing functionality preservation
   - Verify small simulations still work
   - Add performance benchmarks

### Phase 2: Parquet Integration (Day 3-4)
**Goal**: Implement efficient disk-based storage

1. **Parquet Writer Enhancement**
   - Chunked writing with progress
   - Compression options
   - Metadata storage
   - Atomic writes with temp files

2. **Parquet Reader Implementation**
   - Lazy loading iterators
   - Batch reading methods
   - Summary statistics without full load
   - Index for fast patient lookup

3. **Progress Indicators**
   - Saving progress bars
   - Loading progress bars
   - Time estimates
   - Cancellation support

### Phase 3: State Management (Day 5-6)
**Goal**: Robust session and state handling

1. **Session State Cleanup**
   - Automatic old result cleanup
   - Memory-aware cache limits
   - Explicit garbage collection
   - State size monitoring

2. **Simulation Registry**
   - File-based simulation index
   - Metadata storage
   - Multi-tab coordination
   - Cleanup tracking

3. **Checkpoint System**
   - Progress saving during simulation
   - Recovery after crash
   - Partial result handling

### Phase 4: Visualization Adaptation (Day 7-8)
**Goal**: Memory-efficient visualizations

1. **Batch-Aware Charts**
   - Iterator-based plotting
   - Progressive chart building
   - Matplotlib memory management
   - Figure cleanup utilities

2. **Summary Statistics**
   - Pre-computed aggregates
   - Incremental statistics
   - Memory-efficient pandas usage
   - Caching strategy

3. **UI Updates**
   - Show data source (memory/disk)
   - Display patient counts
   - Memory usage indicators
   - Performance metrics

### Phase 5: Robustness (Day 9-10)
**Goal**: Production-ready system

1. **Error Handling**
   - Graceful degradation
   - Clear error messages
   - Recovery suggestions
   - Fallback options

2. **Performance Optimization**
   - Query optimization
   - Caching improvements
   - Parallel processing where safe
   - Memory pool management

3. **Documentation & Testing**
   - User documentation
   - Performance guidelines
   - Load testing
   - Cloud deployment test

## Technical Architecture

### Class Hierarchy
```
SimulationResults (abstract)
├── InMemoryResults
│   ├── Direct patient access
│   ├── Full DataFrame support
│   └── No size limits in API
└── ParquetResults
    ├── Iterator-based access
    ├── Batch processing only
    └── Size-aware methods
```

### File Structure
```
streamlit_app_v2/
├── core/
│   ├── results/
│   │   ├── base.py          # Abstract base class
│   │   ├── memory.py        # In-memory implementation
│   │   └── parquet.py       # Parquet implementation
│   ├── storage/
│   │   ├── writer.py        # Chunked Parquet writer
│   │   ├── reader.py        # Lazy Parquet reader
│   │   └── registry.py      # Simulation registry
│   └── monitoring/
│       ├── memory.py        # Memory monitoring
│       └── progress.py      # Progress indicators
└── tests/
    ├── test_regression.py   # Ensure nothing breaks
    ├── test_memory.py      # Memory behavior tests
    └── test_scale.py       # Large simulation tests
```

### Configuration
```python
# config/memory.py
MEMORY_THRESHOLD_PATIENTS = 1_000
MEMORY_WARNING_MB = 500
MEMORY_CRITICAL_MB = 700
PARQUET_CHUNK_SIZE = 5_000
CACHE_SIZE_MB = 100
MAX_CONCURRENT_SIMS = 3
```

## Implementation Guidelines

### 1. Backward Compatibility
- Existing small simulations must work unchanged
- No API breaks for current visualizations
- Gradual migration path

### 2. Testing Strategy
- Unit tests for each component
- Integration tests for workflows
- Memory leak tests
- Performance benchmarks
- Streamlit Cloud deployment tests

### 3. Code Patterns
```python
# Always use context managers
with SimulationResults.load(sim_id) as results:
    # Process results
    pass  # Auto-cleanup on exit

# Enforce batch processing
for batch in results.iterate_patients(100):
    process_batch(batch)
    
# Explicit memory management
fig = create_plot(data)
st.pyplot(fig)
plt.close(fig)  # Always!
```

### 4. Error Messages
```python
# Clear, actionable errors
if memory_usage > LIMIT:
    st.error(
        "⚠️ Simulation too large for available memory.\n"
        "Options:\n"
        "• Reduce patient count\n"
        "• Reduce simulation duration\n"
        "• Upgrade to Streamlit Cloud paid tier"
    )
```

## Success Criteria

1. **Functionality**: All existing features still work
2. **Scale**: Can simulate 100K patients on free tier
3. **Performance**: < 10 second save/load for 10K patients
4. **Reliability**: No crashes from memory issues
5. **Usability**: Clear feedback and progress indication

## Risk Mitigation

### Risk: Breaking Existing Functionality
**Mitigation**: Comprehensive regression tests before any changes

### Risk: Poor Parquet Performance
**Mitigation**: Benchmark early, optimize chunk sizes

### Risk: Complex API
**Mitigation**: Keep simple operations simple, complexity only when needed

### Risk: User Confusion
**Mitigation**: Clear documentation, helpful error messages

## Future Enhancements

1. **Distributed Processing**: Ready for Dask/Ray integration
2. **Cloud Storage**: S3/GCS for persistent results
3. **Streaming Analytics**: Real-time simulation monitoring
4. **Result Sharing**: Generate shareable links
5. **Comparison Engine**: Compare multiple large simulations

## Timeline

- **Week 1**: Foundation + Parquet Integration
- **Week 2**: State Management + Visualization
- **Testing**: Continuous throughout
- **Documentation**: Progressive updates
- **Deployment Test**: End of Week 2

This plan provides a structured approach to implementing memory-aware architecture while maintaining system stability and user experience.