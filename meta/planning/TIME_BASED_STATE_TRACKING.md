# Time-Based Patient State Tracking Design

## Design Goals
1. **Comprehensive**: Track all time-based state changes
2. **Efficient**: Minimize memory and storage
3. **Queryable**: Fast lookups for analysis
4. **Serializable**: Efficient save/load to Parquet

## Core Design: Event-Based Timeline

Instead of separate lists for visits, state updates, etc., use a unified timeline with typed events.

### Event Types
```python
from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

class EventType(Enum):
    ENROLLMENT = auto()
    STATE_UPDATE = auto()  # Fortnightly disease state change
    VISIT = auto()
    TREATMENT = auto()
    VISION_UPDATE = auto()  # Fortnightly vision change
    DISCONTINUATION = auto()

@dataclass(frozen=True)
class TimelineEvent:
    """Base event in patient timeline."""
    date: datetime
    event_type: EventType
    data: Dict[str, Any]  # Event-specific data
```

### Efficient Patient State Structure
```python
@dataclass
class PatientState:
    """Efficient state tracking for time-based simulation."""
    
    # Identity
    patient_id: str
    enrollment_date: datetime
    baseline_vision: int
    baseline_age: int
    
    # Current state (updated fortnightly)
    current_state: DiseaseState
    actual_vision: float  # True vision value
    vision_ceiling: int
    
    # Timeline - single list of all events
    timeline: List[TimelineEvent]
    
    # Cached aggregates (updated incrementally)
    _injection_count: int = 0
    _last_injection_date: Optional[datetime] = None
    _consecutive_stable_visits: int = 0
    _visits_below_vision_threshold: int = 0
    
    # Discontinuation
    is_discontinued: bool = False
    discontinuation_date: Optional[datetime] = None
    discontinuation_reason: Optional[str] = None
    
    # Efficient lookups
    _last_visit_date: Optional[datetime] = None
    _last_state_update_date: Optional[datetime] = None
    _visits_without_improvement: int = 0
    _best_vision_achieved: float = 0.0
```

### Memory-Efficient Event Storage

```python
# Instead of storing full objects, use compact representations
class CompactEventData:
    """Bit-packed event data for memory efficiency."""
    
    # State updates - store only what changed
    STATE_UPDATE_FIELDS = {
        'new_state': 3,  # 3 bits for 4 disease states
        'treatment_effect': 7,  # 7 bits for 0-100% in steps
    }
    
    # Vision updates - store delta, not absolute
    VISION_UPDATE_FIELDS = {
        'vision_delta': 16,  # 16 bits for ±327.67 letters
        'is_improving': 1,   # 1 bit flag
        'hemorrhage': 1,     # 1 bit flag
    }
    
    # Visits - pack multiple fields
    VISIT_FIELDS = {
        'measured_vision': 7,    # 7 bits for 0-100
        'treatment_given': 1,    # 1 bit
        'interval_days': 8,      # 8 bits for 0-255 days
        'disease_state': 3,      # 3 bits
    }
```

### Sparse Timeline Storage

```python
class SparseTimeline:
    """
    Store only events where something changed.
    Reconstruct full history on demand.
    """
    
    def __init__(self):
        # Store events in sorted list for binary search
        self.events: List[TimelineEvent] = []
        
        # Index for O(1) lookup of specific event types
        self.event_index: Dict[EventType, List[int]] = defaultdict(list)
        
        # Checkpoint states every N events for fast reconstruction
        self.checkpoints: Dict[int, PatientStateSnapshot] = {}
        self.checkpoint_interval = 50
    
    def add_event(self, event: TimelineEvent):
        """Add event and update indices."""
        idx = len(self.events)
        self.events.append(event)
        self.event_index[event.event_type].append(idx)
        
        # Create checkpoint if needed
        if idx % self.checkpoint_interval == 0:
            self.checkpoints[idx] = self._create_snapshot()
    
    def get_state_at(self, date: datetime) -> PatientStateSnapshot:
        """Efficiently reconstruct state at any date."""
        # Binary search for events before date
        idx = bisect_right(self.events, date, key=lambda e: e.date)
        
        # Find nearest checkpoint
        checkpoint_idx = (idx // self.checkpoint_interval) * self.checkpoint_interval
        if checkpoint_idx in self.checkpoints:
            state = copy(self.checkpoints[checkpoint_idx])
            start_idx = checkpoint_idx + 1
        else:
            state = self._initial_state()
            start_idx = 0
        
        # Replay events from checkpoint
        for i in range(start_idx, idx):
            self._apply_event(state, self.events[i])
        
        return state
```

### Optimized Queries

```python
class EfficientPatientQueries:
    """Fast queries on patient data."""
    
    def __init__(self, patient: PatientState):
        self.patient = patient
        self.timeline = SparseTimeline(patient.timeline)
    
    def days_since_last_injection(self, date: datetime) -> Optional[int]:
        """O(1) lookup using cached value."""
        if self.patient._last_injection_date:
            return (date - self.patient._last_injection_date).days
        return None
    
    def injection_rate_last_year(self, date: datetime) -> float:
        """Efficient calculation using event index."""
        year_ago = date - timedelta(days=365)
        
        # Binary search in treatment events only
        treatment_events = self.timeline.event_index[EventType.TREATMENT]
        start_idx = bisect_left(treatment_events, year_ago, 
                               key=lambda i: self.timeline.events[i].date)
        end_idx = bisect_right(treatment_events, date,
                              key=lambda i: self.timeline.events[i].date)
        
        injection_count = sum(
            1 for i in range(start_idx, end_idx)
            if self.timeline.events[treatment_events[i]].data.get('given', False)
        )
        
        return injection_count
    
    def vision_trajectory(self, start_date: datetime, 
                         end_date: datetime) -> List[Tuple[datetime, float]]:
        """Get vision values over time range."""
        # Use vision update events only
        vision_events = self.timeline.event_index[EventType.VISION_UPDATE]
        
        trajectory = []
        current_vision = self.patient.baseline_vision
        
        for idx in vision_events:
            event = self.timeline.events[idx]
            if start_date <= event.date <= end_date:
                current_vision += event.data['vision_delta']
                trajectory.append((event.date, current_vision))
        
        return trajectory
```

### Serialization Strategy

```python
class ParquetSerializer:
    """Efficient serialization to Parquet format."""
    
    @staticmethod
    def serialize_patients(patients: List[PatientState]) -> pd.DataFrame:
        """Convert to columnar format for Parquet."""
        
        # Denormalize timeline events into separate tables
        visits_data = []
        state_updates_data = []
        treatments_data = []
        
        for patient in patients:
            patient_id = patient.patient_id
            
            for event in patient.timeline:
                base_record = {
                    'patient_id': patient_id,
                    'date': event.date,
                }
                
                if event.event_type == EventType.VISIT:
                    visits_data.append({
                        **base_record,
                        'measured_vision': event.data['measured_vision'],
                        'treatment_given': event.data['treatment_given'],
                        'disease_state': event.data['disease_state'],
                    })
                elif event.event_type == EventType.STATE_UPDATE:
                    state_updates_data.append({
                        **base_record,
                        'new_state': event.data['new_state'],
                        'treatment_effect': event.data['treatment_effect'],
                    })
                # ... etc for other event types
        
        # Create separate Parquet files for each event type
        # This allows columnar compression and fast queries
        return {
            'patients': self._create_patient_summary(patients),
            'visits': pd.DataFrame(visits_data),
            'state_updates': pd.DataFrame(state_updates_data),
            'treatments': pd.DataFrame(treatments_data),
        }
```

## Memory Optimization Techniques

### 1. Lazy Loading
```python
class LazyPatientState:
    """Load timeline events only when needed."""
    
    def __init__(self, patient_id: str, summary: dict):
        self.patient_id = patient_id
        self.summary = summary  # Current state, counts, etc.
        self._timeline = None
    
    @property
    def timeline(self):
        if self._timeline is None:
            self._timeline = self._load_timeline()
        return self._timeline
```

### 2. Event Pooling
```python
class EventPool:
    """Reuse event objects to reduce allocations."""
    
    _pools: Dict[EventType, List[TimelineEvent]] = defaultdict(list)
    
    @classmethod
    def get_event(cls, event_type: EventType, date: datetime, 
                  data: dict) -> TimelineEvent:
        pool = cls._pools[event_type]
        if pool:
            event = pool.pop()
            # Reuse object by updating fields
            object.__setattr__(event, 'date', date)
            object.__setattr__(event, 'data', data)
            return event
        return TimelineEvent(date, event_type, data)
```

### 3. Compressed Storage
```python
def compress_timeline(events: List[TimelineEvent]) -> bytes:
    """Compress timeline using domain-specific encoding."""
    
    # Sort by date for delta encoding
    sorted_events = sorted(events, key=lambda e: e.date)
    
    # Encode as deltas
    encoded = []
    last_date = datetime(2024, 1, 1)  # Base date
    
    for event in sorted_events:
        delta_days = (event.date - last_date).days
        encoded.append({
            'delta': delta_days,
            'type': event.event_type.value,
            'data': _encode_event_data(event),
        })
        last_date = event.date
    
    # Use msgpack for efficient binary encoding
    return msgpack.packb(encoded)
```

## Performance Characteristics

### Space Complexity
- **Per Patient**: O(E) where E is number of events
- **Compressed**: ~10-20 bytes per event
- **100K patients × 100 events**: ~100-200 MB

### Time Complexity
- **Add Event**: O(1) amortized
- **Query at Date**: O(log E) with checkpoints
- **Recent Injection**: O(1) with caching
- **Year Statistics**: O(log E + K) where K is events in range

### Serialization
- **Write**: O(N × E) but parallelizable
- **Read**: O(N) for summary, O(E) for full timeline
- **Parquet Compression**: 5-10x reduction typical

## Summary

This design provides:
1. **Unified Timeline**: Single event list reduces complexity
2. **Efficient Queries**: Indices and caching for common operations
3. **Sparse Storage**: Only store changes, not full state
4. **Optimized Serialization**: Columnar format with compression
5. **Lazy Loading**: Load details only when needed
6. **Memory Pooling**: Reuse objects to reduce GC pressure