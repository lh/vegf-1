# Memory Implementation TODOs

## Phase 1: Foundation Infrastructure

### 1. Create Base Results Architecture
- [ ] Create `core/results/` directory structure
- [ ] Implement abstract `SimulationResults` base class
  - [ ] Define abstract methods: `get_patient_count()`, `get_summary_stats()`
  - [ ] Define iterator protocol: `iterate_patients(batch_size)`
  - [ ] Add context manager support (`__enter__`, `__exit__`)
- [ ] Create `ResultsFactory` with automatic tier selection
  - [ ] Define `MEMORY_THRESHOLD_PATIENTS = 1000`
  - [ ] Implement `create_results(n_patients) -> SimulationResults`

### 2. Implement InMemoryResults
- [ ] Create `InMemoryResults` class extending `SimulationResults`
  - [ ] Store patient dictionary directly
  - [ ] Implement `get_all_patients()` method
  - [ ] Implement `to_dataframe()` for easy visualization
  - [ ] Add pickle serialization for session state
- [ ] Write unit tests for InMemoryResults
  - [ ] Test CRUD operations
  - [ ] Test memory usage stays reasonable
  - [ ] Test serialization/deserialization

### 3. Memory Monitoring System
- [ ] Add `psutil` to requirements.txt
- [ ] Create `core/monitoring/memory.py`
  - [ ] Implement `get_memory_usage_mb()`
  - [ ] Implement `get_memory_percentage()`
  - [ ] Create `MemoryMonitor` class with thresholds
- [ ] Add memory display to sidebar
  - [ ] Show current usage with color coding
  - [ ] Green < 70%, Yellow 70-85%, Red > 85%
- [ ] Create memory check decorator
  - [ ] `@check_memory_before` decorator
  - [ ] Prevent operations if memory too high

### 4. Regression Test Suite
- [ ] Create `tests/test_regression.py`
  - [ ] Test existing simulation still runs
  - [ ] Test results still accessible
  - [ ] Test visualizations still work
- [ ] Create `tests/test_compatibility.py`
  - [ ] Ensure old session state format works
  - [ ] Test upgrade path for existing results
- [ ] Set up pytest with memory tracking
  - [ ] Add `pytest-memray` for memory profiling
  - [ ] Create baseline memory benchmarks

## Phase 2: Parquet Implementation

### 5. Enhance Parquet Writer
- [ ] Update existing parquet writer in `simulation_v2/serialization/`
  - [ ] Add chunked writing with configurable chunk size
  - [ ] Implement progress callback mechanism
  - [ ] Add compression options (snappy, gzip, zstd)
  - [ ] Use atomic writes (write to temp, then rename)
- [ ] Add metadata storage
  - [ ] Simulation parameters
  - [ ] Creation timestamp
  - [ ] Patient count and visit statistics
  - [ ] Protocol information

### 6. Implement Parquet Reader
- [ ] Create `ParquetResults` class
  - [ ] Implement lazy loading with pyarrow
  - [ ] Create `iterate_patients(batch_size)` generator
  - [ ] Implement `get_patient_range(start, end)`
  - [ ] Add `get_summary_statistics()` without loading all data
- [ ] Add indexing for fast lookup
  - [ ] Create patient ID index
  - [ ] Enable O(1) patient access
  - [ ] Cache frequently accessed patients

### 7. Progress Indicators
- [ ] Create `core/monitoring/progress.py`
  - [ ] Implement `ProgressTracker` class
  - [ ] Support for both determinate and indeterminate progress
  - [ ] Time estimation based on completion rate
- [ ] Integrate with Streamlit
  - [ ] Use `st.progress()` for visual feedback
  - [ ] Add spinner with descriptive text
  - [ ] Show elapsed and estimated remaining time
- [ ] Add cancellation support
  - [ ] Allow user to stop long operations
  - [ ] Clean up partial results

## Phase 3: State Management

### 8. Session State Cleanup
- [ ] Create `StateManager` class
  - [ ] Track all session state sizes
  - [ ] Implement automatic cleanup of old results
  - [ ] Add explicit `cleanup()` method
- [ ] Add garbage collection triggers
  - [ ] After simulation completion
  - [ ] Before starting new simulation
  - [ ] On memory threshold reached
- [ ] Implement state size limits
  - [ ] Maximum number of stored simulations
  - [ ] Maximum total state size
  - [ ] LRU eviction policy

### 9. Simulation Registry
- [ ] Create `core/storage/registry.py`
  - [ ] File-based registry (JSON format)
  - [ ] Track all simulations with metadata
  - [ ] Support for listing, searching simulations
- [ ] Multi-tab coordination
  - [ ] File locking for concurrent access
  - [ ] Refresh mechanism to see other tabs' simulations
  - [ ] Conflict resolution strategy
- [ ] Cleanup tracking
  - [ ] Mark simulations for cleanup
  - [ ] Background cleanup process
  - [ ] Prevent orphaned files

### 10. Checkpoint System  
- [ ] Design checkpoint format
  - [ ] Partial patient results
  - [ ] Current progress state
  - [ ] Resumable information
- [ ] Implement checkpointing
  - [ ] Save every N patients
  - [ ] Save on graceful shutdown
  - [ ] Atomic checkpoint writes
- [ ] Add recovery mechanism
  - [ ] Detect incomplete simulations
  - [ ] Offer to resume or restart
  - [ ] Merge partial results

## Phase 4: Visualization Adaptation

### 11. Batch-Aware Plotting
- [ ] Create visualization utilities
  - [ ] `BatchPlotter` base class
  - [ ] Incremental plot updates
  - [ ] Memory-efficient aggregations
- [ ] Update existing charts
  - [ ] Modify VA progression chart for batching
  - [ ] Update distribution plots
  - [ ] Adapt time series visualizations
- [ ] Matplotlib memory management
  - [ ] Automatic figure cleanup
  - [ ] Reuse figure objects
  - [ ] Clear axes between updates

### 12. Summary Statistics System
- [ ] Pre-compute during simulation
  - [ ] Running means, std devs
  - [ ] Percentiles using streaming algorithms
  - [ ] Categorical counts
- [ ] Store with Parquet metadata
  - [ ] Quick access without loading data
  - [ ] Version for schema changes
- [ ] Incremental updates
  - [ ] Update stats as patients complete
  - [ ] Merge statistics from batches

### 13. UI Updates
- [ ] Add data source indicators
  - [ ] Show "In Memory" vs "On Disk" badge
  - [ ] Display patient count and visits
  - [ ] Show compression ratio for Parquet
- [ ] Memory usage in UI
  - [ ] Real-time memory gauge
  - [ ] Warnings before operations
  - [ ] Suggest optimizations
- [ ] Performance metrics
  - [ ] Show operation timings
  - [ ] Display throughput (patients/second)
  - [ ] Cache hit rates

## Phase 5: Production Robustness

### 14. Error Handling
- [ ] Graceful memory failures
  - [ ] Catch MemoryError
  - [ ] Offer to reduce batch size
  - [ ] Suggest alternatives
- [ ] Disk space handling
  - [ ] Check available space before write
  - [ ] Estimate space requirements
  - [ ] Cleanup suggestions
- [ ] Network resilience
  - [ ] Handle Streamlit disconnections
  - [ ] Resume interrupted operations
  - [ ] Offline mode support

### 15. Performance Optimization
- [ ] Profile critical paths
  - [ ] Identify bottlenecks
  - [ ] Optimize hot loops
  - [ ] Reduce memory allocations
- [ ] Caching strategy
  - [ ] LRU cache for patient data
  - [ ] Memoize expensive computations
  - [ ] Disk cache for summaries
- [ ] Parallel processing
  - [ ] Use multiprocessing for batch operations
  - [ ] Parallel Parquet writes
  - [ ] Async I/O where possible

### 16. Documentation and Testing
- [ ] User documentation
  - [ ] Memory limits and guidelines
  - [ ] Best practices guide
  - [ ] Troubleshooting section
- [ ] Load testing
  - [ ] Test with 100K patients
  - [ ] Concurrent user testing
  - [ ] Memory leak detection
- [ ] Streamlit Cloud testing
  - [ ] Deploy test version
  - [ ] Verify 1GB limit behavior
  - [ ] Test recovery mechanisms

## Testing Strategy

### Unit Tests (Continuous)
- [ ] Test each new class in isolation
- [ ] Mock dependencies appropriately  
- [ ] Verify memory safety invariants
- [ ] Test error conditions

### Integration Tests (Per Phase)
- [ ] Test complete workflows
- [ ] Verify components work together
- [ ] Test upgrade paths
- [ ] Memory usage under load

### System Tests (End of Phase)
- [ ] Full simulation runs
- [ ] UI interaction testing
- [ ] Performance benchmarks
- [ ] Cloud deployment verification

## Definition of Done

Each TODO is complete when:
1. Code is implemented and working
2. Unit tests pass with >90% coverage  
3. Integration tests verify functionality
4. Documentation is updated
5. No memory leaks detected
6. Performance meets targets
7. Code reviewed and merged

## Progress Tracking

Use GitHub Issues:
- Create issue for each major section
- Link PRs to issues
- Track progress in project board
- Daily updates in main issue

## Risk Log

1. **Parquet performance worse than expected**
   - Mitigation: Benchmark early, have fallback plan

2. **Breaking changes to existing code**
   - Mitigation: Comprehensive test suite first

3. **Complexity overwhelming users**
   - Mitigation: Keep simple path simple

4. **Streamlit Cloud behavior different than local**
   - Mitigation: Test on cloud early and often