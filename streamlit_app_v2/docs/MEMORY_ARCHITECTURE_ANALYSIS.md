# Memory Architecture Analysis for APE V2

## Executive Summary

This document captures our comprehensive analysis of memory constraints and architectural decisions for deploying APE V2 on Streamlit Cloud. Through three iterations of analysis, we've identified critical constraints and designed a robust solution using a two-tier storage system with Parquet as a forcing function for memory-safe development.

## The Memory Challenge

### Initial Question
"How big can simulations get before memory problems occur?"

### Streamlit Cloud Free Tier Constraints
- **Total RAM**: 1GB
- **Streamlit Framework**: ~200-300MB
- **Available for App**: ~700-800MB
- **Safe Operating Limit**: ~500MB
- **Container Behavior**: Killed immediately if limit exceeded (no graceful degradation)

## Memory Usage Analysis

### Per-Patient Memory Footprint

#### First Estimate (Optimistic)
```
Patient object:
├── Basic attributes: ~200 bytes
├── Per visit: ~372 bytes
├── Per patient-year: ~3.7KB
└── 100K patients × 5 years = 1.85GB
```

#### Revised Estimate (Realistic)
```
Patient object with Python overhead:
├── Basic attributes: ~500 bytes
├── Per visit: ~500-600 bytes
├── Per patient-year: ~5-6KB
├── With visualization prep: ~10KB/patient-year
└── 100K patients × 5 years = 5GB (!)
```

### Safe Simulation Limits for Streamlit Cloud
- **Maximum Safe**: ~10,000 patient-years total
- **Examples**:
  - 5,000 patients × 2 years ✓
  - 2,000 patients × 5 years ✓
  - 10,000 patients × 5 years ✗ (500MB+)

## Hidden Memory Challenges

### 1. Streamlit Session State Accumulation
```python
st.session_state.simulation_results = {...}  # Never cleaned!
# Multiple runs = memory accumulation
# Each page navigation preserves state
```

### 2. Visualization Memory Multiplication
```python
# Original data: 50MB
df = pd.DataFrame(patient_histories)  # +50MB
df_melted = df.melt()  # +100MB
fig, ax = plt.subplots()  # +20MB
# Total: 220MB for one chart!
```

### 3. The Rerun Problem
- Every button click = full script rerun
- Potential simulation re-execution
- Need explicit guards against duplicate runs

### 4. Multi-Tab Coordination
- Each browser tab = separate session state
- No awareness between tabs
- Potential duplicate simulations

### 5. Progress Loss Scenarios
- Browser refresh
- Container restart
- Network disconnect
- No checkpoint/recovery system

### 6. Memory Leaks
```python
# Matplotlib leak example
plt.plot(data)
st.pyplot()  # Figure never closed!

# Correct approach
fig, ax = plt.subplots()
ax.plot(data)
st.pyplot(fig)
plt.close(fig)  # Critical!
```

### 7. Time-Based Issues
- System clock changes
- Daylight saving transitions
- UTC vs local time confusion
- Need monotonic time for durations

### 8. Concurrent User Scaling
- 100 users × 5K patients = 5GB RAM needed
- Free tier = instant failure
- Need queuing or limits

### 9. Mobile Device Constraints
- Significantly less memory
- Aggressive tab killing
- Need ultra-light mode

### 10. Write Performance
- Parquet writes can take 5-10 seconds
- UI freezes during write
- Need progress indication

## Architectural Solution

### Core Principle
"Don't make memory awareness optional - make memory waste impossible."

### Two-Tier Storage System

#### Tier 1: InMemoryResults (< 1,000 patients)
```python
class InMemoryResults:
    def get_all_patients(self) -> Dict[str, Patient]
    def to_dataframe(self) -> pd.DataFrame
    # Direct, fast access for small simulations
```

#### Tier 2: ParquetResults (≥ 1,000 patients)
```python
class ParquetResults:
    def iterate_patients(self, batch_size=100) -> Iterator[List[Patient]]
    def get_patient_range(self, start, end) -> List[Patient]
    def get_summary_statistics(self) -> Dict
    # NO get_all_patients() method - enforces batching!
```

### Automatic Selection
```python
def create_results(n_patients: int) -> SimulationResults:
    if n_patients < MEMORY_THRESHOLD:
        return InMemoryResults()
    return ParquetResults()
```

### Why Parquet as Forcing Function

1. **Architectural Enforcement**: Can't accidentally load everything
2. **Natural Batching**: All features must handle iterators
3. **Real Testing**: Can actually test 100K patient simulations
4. **Compression**: 5-10x smaller than JSON
5. **Performance**: Columnar format ideal for analytics

### Memory Safety Patterns

#### Batch Processing
```python
# Instead of:
all_patients = results.get_all_patients()  # 💥 Boom!

# Enforce:
for batch in results.iterate_patients(batch_size=100):
    process_batch(batch)
```

#### Progressive Visualization
```python
# Build charts incrementally
fig, ax = plt.subplots()
for batch in results.iterate_patients():
    update_plot(ax, batch)
plt.close(fig)  # Always cleanup!
```

#### State Management
```python
# Automatic cleanup
if 'previous_results' in st.session_state:
    del st.session_state.previous_results
    gc.collect()
```

## Storage Tiers

### Hot (In-Memory)
- Current simulation
- Recent summary statistics
- Active visualizations

### Warm (Local Parquet)
- Today's simulations
- Quick access via indexes
- Compressed storage

### Cold (Archived)
- Older results
- Maximum compression
- Infrequent access

## Critical Implementation Details

### Progress Feedback
```python
with st.spinner("Saving results..."):
    progress = st.progress(0)
    for i, chunk in enumerate(chunks):
        save_chunk(chunk)
        progress.progress((i+1)/total_chunks)
```

### Memory Monitoring
```python
import psutil

def check_memory():
    mb_used = psutil.Process().memory_info().rss / 1024 / 1024
    if mb_used > 500:
        st.warning(f"⚠️ High memory: {mb_used:.0f}MB")
```

### Checkpoint System
```python
class SimulationCheckpoint:
    def save_progress(self, patients_done: int):
        # Enable recovery after crash
```

### Resource Limits
```python
MEMORY_WARNING_THRESHOLD = 10_000  # patients
MEMORY_AUTO_DISK_THRESHOLD = 50_000
CHUNK_SIZE = 5_000
MAX_CONCURRENT_SIMULATIONS = 3
```

## Benefits of This Architecture

1. **Impossible to Break**: Memory-unsafe operations don't exist
2. **Automatic Scaling**: Same code for 100 or 100K patients  
3. **Testing Reality**: Can test production-scale locally
4. **Future Proof**: Ready for distributed processing
5. **User Friendly**: Graceful degradation with feedback

## Conclusion

By implementing Parquet infrastructure as a forcing function, we create a system where:
- Small simulations remain fast and simple
- Large simulations work automatically
- Memory safety is architecturally enforced
- Future features inherit scalability

This approach transforms memory constraints from a limitation to be worked around into a design principle that guides better architecture.