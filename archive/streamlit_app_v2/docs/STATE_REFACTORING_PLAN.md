# State Management Refactoring Plan

## Vision: Multi-Simulation Comparison

The architecture must support:
- Loading multiple simulations simultaneously
- Comparing 2+ simulations side-by-side
- Mixing fresh runs with historical data
- Efficient memory management for large datasets
- Clear data provenance and identification

## Proposed Architecture

### 1. Core State Structure

```python
# Session state will have a simulation registry, not just one simulation
st.session_state = {
    # Registry of all loaded simulations (limited by memory)
    'simulation_registry': {
        'sim_id_1': SimulationData,
        'sim_id_2': SimulationData,
        # ... up to MAX_LOADED_SIMULATIONS
    },
    
    # Currently active simulation for single-view pages
    'active_sim_id': 'sim_id_1',
    
    # Simulations selected for comparison
    'comparison_sim_ids': ['sim_id_1', 'sim_id_2'],
    
    # Current protocol (for running new simulations)
    'current_protocol': ProtocolData,
    
    # UI state (kept separate from data)
    'ui_state': UIState,
}
```

### 2. Unified Data Model

```python
@dataclass
class SimulationData:
    """Complete data for one simulation"""
    # Identity
    sim_id: str
    source: Literal['fresh', 'loaded', 'imported']
    
    # Core data
    results: SimulationResults  # The actual results object
    protocol: ProtocolData      # Full protocol including spec
    parameters: SimulationParameters
    audit_log: List[AuditEvent]
    
    # Metadata
    created_at: datetime
    loaded_at: datetime
    runtime_seconds: float
    memory_usage_mb: float
    
    # State
    is_pinned: bool = False  # Keep in memory even if not active
    last_accessed: datetime = field(default_factory=datetime.now)

@dataclass 
class ProtocolData:
    """Complete protocol information"""
    name: str
    version: str
    path: Optional[Path]
    spec: ProtocolSpecification
    checksum: str

@dataclass
class SimulationParameters:
    """Simulation run parameters"""
    engine: Literal['abs', 'des']
    n_patients: int
    duration_years: float
    seed: int
```

### 3. State Management Service

```python
class SimulationStateService:
    """Central service for all simulation state management"""
    
    MAX_LOADED_SIMULATIONS = 5  # Configurable based on memory
    
    @staticmethod
    def load_simulation(sim_id: str, set_as_active: bool = True) -> SimulationData:
        """Load a simulation into the registry"""
        # Check if already loaded
        registry = st.session_state.get('simulation_registry', {})
        if sim_id in registry:
            if set_as_active:
                st.session_state['active_sim_id'] = sim_id
            return registry[sim_id]
        
        # Load from disk
        sim_data = SimulationStateService._load_from_disk(sim_id)
        
        # Add to registry (with memory management)
        SimulationStateService._add_to_registry(sim_data)
        
        if set_as_active:
            st.session_state['active_sim_id'] = sim_id
            
        return sim_data
    
    @staticmethod
    def run_simulation(protocol: ProtocolData, params: SimulationParameters) -> SimulationData:
        """Run a new simulation and add to registry"""
        # Run simulation
        results = SimulationEngine.run(protocol.spec, params)
        
        # Create SimulationData
        sim_data = SimulationData(
            sim_id=results.metadata.sim_id,
            source='fresh',
            results=results,
            protocol=protocol,
            parameters=params,
            audit_log=results.audit_log,
            created_at=datetime.now(),
            loaded_at=datetime.now(),
            runtime_seconds=results.runtime_seconds,
            memory_usage_mb=results.get_memory_usage_mb()
        )
        
        # Add to registry and set as active
        SimulationStateService._add_to_registry(sim_data)
        st.session_state['active_sim_id'] = sim_data.sim_id
        
        return sim_data
    
    @staticmethod
    def get_active_simulation() -> Optional[SimulationData]:
        """Get the currently active simulation"""
        active_id = st.session_state.get('active_sim_id')
        if not active_id:
            return None
        return st.session_state.get('simulation_registry', {}).get(active_id)
    
    @staticmethod
    def set_comparison_simulations(sim_ids: List[str]):
        """Set simulations for comparison view"""
        # Ensure all are loaded
        for sim_id in sim_ids:
            SimulationStateService.load_simulation(sim_id, set_as_active=False)
        
        st.session_state['comparison_sim_ids'] = sim_ids
    
    @staticmethod
    def _add_to_registry(sim_data: SimulationData):
        """Add simulation to registry with memory management"""
        registry = st.session_state.get('simulation_registry', {})
        
        # Check memory limits
        if len(registry) >= SimulationStateService.MAX_LOADED_SIMULATIONS:
            # Evict least recently used, non-pinned simulation
            SimulationStateService._evict_lru_simulation()
        
        registry[sim_data.sim_id] = sim_data
        st.session_state['simulation_registry'] = registry
    
    @staticmethod
    def _evict_lru_simulation():
        """Remove least recently used simulation from memory"""
        registry = st.session_state.get('simulation_registry', {})
        
        # Find LRU non-pinned simulation
        candidates = [
            (sim_id, data) for sim_id, data in registry.items()
            if not data.is_pinned and sim_id != st.session_state.get('active_sim_id')
        ]
        
        if candidates:
            lru_sim = min(candidates, key=lambda x: x[1].last_accessed)
            del registry[lru_sim[0]]
```

### 4. Import/Export Service

```python
class SimulationIOService:
    """Handles all import/export operations"""
    
    @staticmethod
    def export_simulation(sim_id: str) -> bytes:
        """Export a simulation from the registry"""
        sim_data = SimulationStateService.get_simulation(sim_id)
        if not sim_data:
            raise ValueError(f"Simulation {sim_id} not found")
        
        # Create package
        package = SimulationPackage.create(sim_data)
        return package.to_bytes()
    
    @staticmethod
    def import_simulation(package_data: bytes) -> SimulationData:
        """Import a simulation and add to registry"""
        # Unpack
        package = SimulationPackage.from_bytes(package_data)
        sim_data = package.to_simulation_data()
        
        # Mark as imported
        sim_data.source = 'imported'
        
        # Add to registry and activate
        SimulationStateService._add_to_registry(sim_data)
        st.session_state['active_sim_id'] = sim_data.sim_id
        
        return sim_data
```

### 5. Page Integration Examples

```python
# In 2_Simulations.py
def run_simulation():
    protocol = st.session_state.get('current_protocol')
    params = get_simulation_parameters()
    
    # Run and automatically add to registry
    sim_data = SimulationStateService.run_simulation(protocol, params)
    
    # UI automatically updates because it reads from registry

# In 3_Analysis_Overview.py  
def show_analysis():
    # Single simulation view
    sim_data = SimulationStateService.get_active_simulation()
    if not sim_data:
        st.error("No simulation selected")
        return
    
    display_simulation(sim_data)

# Future: Comparison view
def show_comparison():
    sim_ids = st.session_state.get('comparison_sim_ids', [])
    simulations = [
        SimulationStateService.get_simulation(sim_id) 
        for sim_id in sim_ids
    ]
    
    display_comparison(simulations)
```

## Migration Strategy

### Phase 1: Create New Services (Week 1)
1. Implement SimulationData model
2. Create SimulationStateService
3. Create SimulationIOService
4. Add comprehensive tests

### Phase 2: Parallel Implementation (Week 2)
1. Update import/export to use new services
2. Add service calls alongside existing code
3. Verify data consistency

### Phase 3: Page Migration (Week 3)
1. Migrate Protocol Manager
2. Migrate Simulations page
3. Migrate Analysis Overview
4. Remove old state management

### Phase 4: Comparison Features (Future)
1. Add comparison UI
2. Implement multi-simulation views
3. Add diff capabilities

## Benefits

1. **Scalability**: Ready for multi-simulation comparison
2. **Consistency**: Single source of truth for all data
3. **Memory Management**: Automatic eviction of old data
4. **Clear Contracts**: Type-safe data structures
5. **Testability**: Services can be tested independently
6. **Future-Proof**: Easy to add persistence, caching, etc.

## Implementation Notes

1. Start with SimulationData model - get the data structure right first
2. Use dependency injection for services to aid testing
3. Add logging at service boundaries for debugging
4. Consider using Streamlit's cache for read-only operations
5. Plan for WebSocket updates when comparing live simulations