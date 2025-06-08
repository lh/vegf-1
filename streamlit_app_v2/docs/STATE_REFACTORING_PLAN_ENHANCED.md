# Enhanced State Management Refactoring Plan

## Vision: Enterprise-Ready Multi-Simulation Platform

Building on the original plan, these enhancements address scalability, performance, and future extensibility needs.

## Enhanced Architecture Components

### 1. Two-Tier Data Loading

```python
@dataclass
class SimulationMetadata:
    """Lightweight metadata always kept in memory"""
    sim_id: str
    created_at: datetime
    n_patients: int
    duration_years: float
    protocol_name: str
    protocol_version: str
    file_size_mb: float
    checksum: str
    tags: List[str]
    last_accessed: datetime
    access_count: int
    
@dataclass
class SimulationData:
    """Full simulation data - lazy loaded on demand"""
    metadata: SimulationMetadata
    results: Optional[SimulationResults] = None  # Lazy loaded
    protocol: Optional[ProtocolData] = None      # Lazy loaded
    audit_log: Optional[List[AuditEvent]] = None # Lazy loaded
    
    def load_results(self) -> SimulationResults:
        """Load results data on demand"""
        if self.results is None:
            self.results = ResultsFactory.load_results(self.metadata.sim_id)
        return self.results
    
    def unload_results(self):
        """Free memory by unloading results"""
        self.results = None
```

### 2. Transactional State Management

```python
class StateTransaction:
    """Ensure atomic state updates with rollback capability"""
    
    def __init__(self, state_service: SimulationStateService):
        self.state_service = state_service
        self.original_state = {}
        self.operations = []
    
    def __enter__(self):
        # Snapshot current state
        self.original_state = self._snapshot_state()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Rollback on error
            self._restore_state(self.original_state)
            logger.error(f"State transaction failed, rolled back: {exc_val}")
        return False
    
    def add_simulation(self, sim_data: SimulationData):
        """Add operation to transaction"""
        self.operations.append(('add', sim_data))
    
    def commit(self):
        """Execute all operations atomically"""
        for op_type, data in self.operations:
            if op_type == 'add':
                self.state_service._add_to_registry(data)
```

### 3. Event-Driven Architecture

```python
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Dict, List

class EventType(Enum):
    SIMULATION_LOADED = "simulation_loaded"
    SIMULATION_EVICTED = "simulation_evicted"
    COMPARISON_STARTED = "comparison_started"
    MEMORY_THRESHOLD_REACHED = "memory_threshold_reached"
    STATE_CORRUPTED = "state_corrupted"
    SEARCH_PERFORMED = "search_performed"

@dataclass
class SimulationEvent:
    type: EventType
    simulation_id: Optional[str]
    data: Dict
    timestamp: datetime
    user_id: Optional[str]

class EventBus:
    """Central event system for state changes"""
    
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable]] = {}
        self.event_history: List[SimulationEvent] = []
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to events"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def publish(self, event: SimulationEvent):
        """Publish event to all listeners"""
        self.event_history.append(event)
        
        # Async notification to avoid blocking
        for listener in self.listeners.get(event.type, []):
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Event listener failed: {e}")
```

### 4. Advanced Comparison Service

```python
class ComparisonService:
    """Sophisticated multi-simulation comparison"""
    
    def __init__(self, state_service: SimulationStateService):
        self.state_service = state_service
        self.comparison_cache = {}
    
    def compare_simulations(
        self,
        sim_ids: List[str],
        comparison_type: Literal['overlay', 'side_by_side', 'difference', 'statistical'],
        metrics: List[str] = None,
        time_alignment: Literal['absolute', 'relative', 'normalized'] = 'absolute'
    ) -> ComparisonResult:
        """Compare multiple simulations with various modes"""
        
        # Load simulations efficiently
        simulations = []
        for sim_id in sim_ids:
            sim_data = self.state_service.get_simulation(sim_id)
            if sim_data:
                simulations.append(sim_data)
        
        # Align time scales if needed
        if time_alignment != 'absolute':
            simulations = self._align_timescales(simulations, time_alignment)
        
        # Perform comparison based on type
        if comparison_type == 'overlay':
            return self._overlay_comparison(simulations, metrics)
        elif comparison_type == 'difference':
            return self._difference_comparison(simulations, metrics)
        # ... etc
    
    def _align_timescales(self, simulations: List[SimulationData], mode: str):
        """Align simulations with different time scales"""
        # Implementation for time alignment
        pass
```

### 5. Search and Discovery

```python
class SimulationSearchService:
    """Full-featured search across simulation registry"""
    
    def __init__(self, state_service: SimulationStateService):
        self.state_service = state_service
        self.search_index = {}  # In-memory search index
    
    def search(
        self,
        query: str = None,
        filters: Dict = None,
        sort_by: str = 'created_at',
        limit: int = 20
    ) -> List[SimulationMetadata]:
        """Search simulations with filters and sorting"""
        
        results = []
        
        # Get all metadata (lightweight)
        all_metadata = self.state_service.get_all_metadata()
        
        # Apply text search if query provided
        if query:
            results = self._text_search(all_metadata, query)
        else:
            results = all_metadata
        
        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)
        
        # Sort results
        results = self._sort_results(results, sort_by)
        
        # Limit results
        return results[:limit]
    
    def add_tag(self, sim_id: str, tag: str):
        """Add tag to simulation for organization"""
        self.state_service.update_metadata(
            sim_id, 
            lambda m: m.tags.append(tag)
        )
```

### 6. Performance Monitoring

```python
class PerformanceMonitor:
    """Track and optimize system performance"""
    
    def __init__(self):
        self.metrics = {
            'load_times': {},
            'memory_usage': {},
            'cache_hits': 0,
            'cache_misses': 0,
            'eviction_count': 0,
            'access_patterns': {}
        }
    
    def record_load_time(self, sim_id: str, duration: float):
        """Track simulation load times"""
        if sim_id not in self.metrics['load_times']:
            self.metrics['load_times'][sim_id] = []
        self.metrics['load_times'][sim_id].append(duration)
    
    def get_optimization_suggestions(self) -> List[str]:
        """Analyze metrics and suggest optimizations"""
        suggestions = []
        
        # Check for frequently accessed simulations
        frequent_sims = self._get_frequent_simulations()
        if frequent_sims:
            suggestions.append(
                f"Pin these frequently accessed simulations: {frequent_sims}"
            )
        
        # Check cache performance
        if self.metrics['cache_hits'] + self.metrics['cache_misses'] > 0:
            hit_rate = self.metrics['cache_hits'] / (
                self.metrics['cache_hits'] + self.metrics['cache_misses']
            )
            if hit_rate < 0.7:
                suggestions.append(
                    f"Low cache hit rate ({hit_rate:.1%}). Consider increasing cache size."
                )
        
        return suggestions
```

### 7. Schema Versioning and Migration

```python
class SchemaVersion:
    """Track and manage data schema versions"""
    CURRENT_VERSION = "2.0.0"
    
    MIGRATIONS = {
        "1.0.0": "migrate_v1_to_v2",
        "1.5.0": "migrate_v1_5_to_v2",
    }

class MigrationService:
    """Handle data migrations between versions"""
    
    def migrate_simulation_data(self, data: Dict, from_version: str) -> Dict:
        """Migrate data to current version"""
        current = from_version
        
        while current != SchemaVersion.CURRENT_VERSION:
            if current not in SchemaVersion.MIGRATIONS:
                raise ValueError(f"No migration path from {current}")
            
            migration_func = getattr(self, SchemaVersion.MIGRATIONS[current])
            data = migration_func(data)
            current = self._get_next_version(current)
        
        return data
    
    def migrate_v1_to_v2(self, data: Dict) -> Dict:
        """Specific migration from v1 to v2"""
        # Add new required fields
        data['schema_version'] = "2.0.0"
        data['tags'] = []
        data['access_count'] = 0
        return data
```

### 8. Persistent Cache Layer

```python
class PersistentCache:
    """Cache that survives server restarts"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_db = self.cache_dir / "metadata.db"
        self._init_db()
    
    def save_metadata(self, metadata: SimulationMetadata):
        """Persist metadata to disk"""
        # Use SQLite for fast queries
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO simulation_metadata
                (sim_id, created_at, n_patients, duration_years, 
                 protocol_name, tags, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.sim_id,
                metadata.created_at.isoformat(),
                metadata.n_patients,
                metadata.duration_years,
                metadata.protocol_name,
                json.dumps(metadata.tags),
                metadata.last_accessed.isoformat()
            ))
    
    def load_all_metadata(self) -> List[SimulationMetadata]:
        """Load all metadata from cache"""
        # Implementation
        pass
```

### 9. Enhanced State Service

```python
class EnhancedSimulationStateService(SimulationStateService):
    """Extended state service with all enhancements"""
    
    def __init__(self):
        super().__init__()
        self.metadata_registry: Dict[str, SimulationMetadata] = {}
        self.event_bus = EventBus()
        self.performance_monitor = PerformanceMonitor()
        self.search_service = SimulationSearchService(self)
        self.comparison_service = ComparisonService(self)
        self.persistent_cache = PersistentCache(Path("~/.ape_cache"))
        
        # Load metadata from persistent cache on startup
        self._load_cached_metadata()
    
    def load_simulation(self, sim_id: str, load_data: bool = False) -> SimulationData:
        """Load simulation with optional data loading"""
        start_time = time.time()
        
        # Check if metadata is already loaded
        if sim_id in self.metadata_registry:
            metadata = self.metadata_registry[sim_id]
            sim_data = SimulationData(metadata=metadata)
            
            if load_data:
                sim_data.load_results()
            
            # Update access tracking
            metadata.last_accessed = datetime.now()
            metadata.access_count += 1
            
        else:
            # Load from disk
            sim_data = self._load_from_disk(sim_id)
            self.metadata_registry[sim_id] = sim_data.metadata
        
        # Record performance
        duration = time.time() - start_time
        self.performance_monitor.record_load_time(sim_id, duration)
        
        # Publish event
        self.event_bus.publish(SimulationEvent(
            type=EventType.SIMULATION_LOADED,
            simulation_id=sim_id,
            data={'load_time': duration, 'with_data': load_data},
            timestamp=datetime.now(),
            user_id=self._get_current_user()
        ))
        
        return sim_data
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage by simulation"""
        usage = {}
        for sim_id, sim_data in self.simulation_registry.items():
            if sim_data.results is not None:
                usage[sim_id] = sim_data.results.get_memory_usage_mb()
        return usage
    
    def optimize_memory(self):
        """Run memory optimization based on usage patterns"""
        suggestions = self.performance_monitor.get_optimization_suggestions()
        
        # Auto-pin frequently accessed simulations
        frequent_sims = self._get_frequently_accessed_simulations()
        for sim_id in frequent_sims:
            if sim_id in self.simulation_registry:
                self.simulation_registry[sim_id].is_pinned = True
        
        # Unload data for inactive simulations
        for sim_id, sim_data in self.simulation_registry.items():
            if not sim_data.is_pinned and sim_data.results is not None:
                last_access = sim_data.metadata.last_accessed
                if (datetime.now() - last_access).seconds > 3600:  # 1 hour
                    sim_data.unload_results()
```

## Implementation Phases (Revised)

### Phase 1: Core Infrastructure (Week 1-2)
1. Implement SimulationMetadata and two-tier loading
2. Create EventBus and basic event system
3. Add StateTransaction for atomic operations
4. Set up PersistentCache with SQLite

### Phase 2: Enhanced Services (Week 2-3)
1. Build SearchService with indexing
2. Implement ComparisonService foundations
3. Add PerformanceMonitor
4. Create MigrationService

### Phase 3: Integration (Week 3-4)
1. Migrate existing pages to new services
2. Add event listeners for UI updates
3. Implement lazy loading in UI components
4. Add search/filter UI elements

### Phase 4: Advanced Features (Week 4-5)
1. Full comparison UI implementation
2. Performance dashboard
3. Advanced caching strategies
4. Multi-user coordination

## Key Benefits of Enhancements

1. **Scalability**: Can handle 100s of simulations with millions of patients
2. **Performance**: Lazy loading and intelligent caching reduce memory pressure
3. **Reliability**: Transactional updates prevent corruption
4. **Extensibility**: Event system allows easy feature additions
5. **Usability**: Search and tagging make finding simulations easy
6. **Monitoring**: Built-in performance tracking for optimization
7. **Future-Proof**: Schema versioning handles evolution
8. **Multi-User**: Proper coordination for team environments

## Risk Mitigation

1. **Gradual Migration**: Keep old system running in parallel
2. **Feature Flags**: Roll out enhancements incrementally
3. **Comprehensive Testing**: Each phase fully tested before proceeding
4. **Rollback Plan**: Can revert to previous version if needed
5. **Performance Benchmarks**: Ensure no regression in speed

## Success Metrics

1. Load time for 100k patient simulation < 2 seconds
2. Memory usage reduced by 60% for multi-simulation scenarios
3. Zero data corruption incidents
4. Search results returned in < 100ms
5. Comparison views render in < 1 second