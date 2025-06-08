# Economic Analysis Implementation Plan (ARCHIVED 2025-06-07)

**ARCHIVED DOCUMENT**: This implementation guide was superseded on June 7, 2025. Kept for historical reference to understand previous design decisions and implementation approaches.

**ORIGINAL HEADER**: This was the active implementation guide. Read and follow this document when implementing economic features. It provides the concrete roadmap based on decisions from ECONOMIC_ANALYSIS_PLANNING.md and uses the TDD approach outlined in TDD_ECONOMIC_PLAN.md.

Based on the design decisions from ECONOMIC_ANALYSIS_PLANNING.md, this document provides a concrete implementation roadmap.

## Overview

We will implement a non-invasive cost tracking system that:
- Uses YAML configuration files for cost parameters
- Adds optional metadata to existing visit structures
- Provides a separate cost analysis layer
- Exports results in Parquet format for Streamlit integration

## Development Approach

We are following Test-Driven Development (TDD) methodology as documented in [TDD_ECONOMIC_PLAN.md](TDD_ECONOMIC_PLAN.md). All features will be developed by:
1. Writing failing tests first
2. Implementing minimal code to pass tests
3. Refactoring while keeping tests green

This ensures high code quality and prevents regression in existing functionality.

## Phase 1: Core Cost Infrastructure (Week 1)

### 1.1 Directory Structure
```
protocols/
  cost_configs/
    nhs_standard_2025.yaml
    nhs_standard_2025_test.yaml
    components/
      drug_costs.yaml
      visit_components.yaml
    
simulation/
  economics/
    __init__.py
    cost_config.py
    cost_analyzer.py
    cost_tracker.py
    
tests/
  fixtures/
    economics/
      test_cost_config.yaml
      sample_patient_history.json
      expected_cost_events.json
  unit/
    test_cost_config.py
    test_cost_analyzer.py
    test_cost_tracker.py
  integration/
    test_economic_integration.py
```

### 1.2 Cost Configuration Schema

**File: `protocols/cost_configs/nhs_standard_2025.yaml`**
```yaml
# NHS Standard Costs 2025
metadata:
  name: "NHS Standard Costs 2025"
  currency: "GBP"
  effective_date: "2025-01-01"
  version: "1.0"

# Drug costs per administration
drug_costs:
  eylea_2mg: 800
  eylea_8mg: 800  # Placeholder
  avastin: 50     # Off-label
  lucentis: 600

# Component costs
visit_components:
  # Clinical activities
  injection: 150
  oct_scan: 75
  visual_acuity_test: 25
  pressure_check: 10
  
  # Review types
  virtual_review: 50
  face_to_face_review: 120
  nurse_review: 40
  
  # Additional components
  adverse_event_assessment: 200
  fluorescein_angiography: 150

# Visit type definitions (compositions)
visit_types:
  injection_virtual:
    components: [injection, oct_scan, pressure_check, virtual_review]
    total_override: null  # Use sum of components
    
  injection_loading:
    components: [injection, visual_acuity_test]
    total_override: null
    
  monitoring_virtual:
    components: [oct_scan, visual_acuity_test, virtual_review]
    total_override: null
    
  monitoring_face_to_face:
    components: [oct_scan, visual_acuity_test, pressure_check, face_to_face_review]
    total_override: null

# Special event costs
special_events:
  initial_assessment: 250
  discontinuation_admin: 50
  retreatment_assessment: 200
  adverse_event_mild: 500
  adverse_event_severe: 2000
```

### 1.3 Core Classes

**File: `simulation/economics/cost_config.py`**
```python
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CostConfig:
    """Holds cost configuration data"""
    metadata: Dict[str, Any]
    drug_costs: Dict[str, float]
    visit_components: Dict[str, float]
    visit_types: Dict[str, Dict[str, Any]]
    special_events: Dict[str, float]
    
    @classmethod
    def from_yaml(cls, filepath: Path) -> 'CostConfig':
        """Load cost configuration from YAML file"""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def get_drug_cost(self, drug_name: str) -> float:
        """Get cost for a specific drug"""
        return self.drug_costs.get(drug_name, 0.0)
    
    def get_visit_cost(self, visit_type: str) -> float:
        """Calculate total cost for a visit type"""
        if visit_type not in self.visit_types:
            return 0.0
            
        visit_def = self.visit_types[visit_type]
        
        # Check for override
        if visit_def.get('total_override') is not None:
            return visit_def['total_override']
            
        # Sum component costs
        total = 0.0
        for component in visit_def.get('components', []):
            total += self.visit_components.get(component, 0.0)
            
        return total
```

**File: `simulation/economics/cost_analyzer.py`**
```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from .cost_config import CostConfig

@dataclass
class CostEvent:
    """Represents a single cost event"""
    time: float
    patient_id: str
    event_type: str  # 'drug', 'visit', 'special'
    category: str    # specific drug/visit type
    amount: float
    components: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class CostAnalyzer:
    """Analyzes patient histories and calculates costs"""
    
    def __init__(self, cost_config: CostConfig):
        self.config = cost_config
        
    def analyze_visit(self, visit: Dict[str, Any]) -> Optional[CostEvent]:
        """Analyze a single visit and return cost event"""
        
        # Determine visit components
        components = self._determine_components(visit)
        if not components:
            return None
            
        # Calculate costs
        component_costs = {}
        total_cost = 0.0
        
        for component in components:
            cost = self.config.visit_components.get(component, 0.0)
            component_costs[component] = cost
            total_cost += cost
            
        # Add drug cost if injection
        drug_cost = 0.0
        if 'injection' in components and 'drug' in visit:
            drug_cost = self.config.get_drug_cost(visit['drug'])
            total_cost += drug_cost
            
        return CostEvent(
            time=visit['time'],
            patient_id=visit.get('patient_id', 'unknown'),
            event_type='visit',
            category=visit.get('metadata', {}).get('visit_subtype', visit['type']),
            amount=total_cost,
            components=component_costs,
            metadata={
                'drug_cost': drug_cost,
                'visit_cost': total_cost - drug_cost,
                'phase': visit.get('metadata', {}).get('phase', 'unknown')
            }
        )
    
    def _determine_components(self, visit: Dict[str, Any]) -> List[str]:
        """Determine visit components from metadata or inference"""
        
        # Check metadata first
        metadata = visit.get('metadata', {})
        if 'components_performed' in metadata:
            return metadata['components_performed']
            
        # Check for visit subtype
        if 'visit_subtype' in metadata:
            visit_type = metadata['visit_subtype']
            if visit_type in self.config.visit_types:
                return self.config.visit_types[visit_type]['components']
                
        # Fallback to inference based on visit type and phase
        return self._infer_components(visit)
    
    def _infer_components(self, visit: Dict[str, Any]) -> List[str]:
        """Infer components from visit type and context"""
        visit_type = visit.get('type', '')
        phase = visit.get('metadata', {}).get('phase', '')
        
        # Simple inference rules (to be expanded)
        if visit_type == 'injection':
            if phase == 'loading':
                return ['injection', 'visual_acuity_test']
            else:
                return ['injection', 'oct_scan', 'pressure_check', 'virtual_review']
                
        elif visit_type == 'monitoring':
            return ['oct_scan', 'visual_acuity_test', 'virtual_review']
            
        return []
    
    def analyze_patient_history(self, patient_history: Dict[str, Any]) -> List[CostEvent]:
        """Analyze complete patient history and return all cost events"""
        cost_events = []
        
        # Process each visit
        for visit in patient_history.get('visits', []):
            cost_event = self.analyze_visit(visit)
            if cost_event:
                cost_event.patient_id = patient_history.get('patient_id', 'unknown')
                cost_events.append(cost_event)
                
        # Add special events (e.g., initial assessment, discontinuation)
        # TODO: Implement special event detection
        
        return cost_events
```

**File: `simulation/economics/cost_tracker.py`**
```python
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
from .cost_analyzer import CostAnalyzer, CostEvent

class CostTracker:
    """Tracks and aggregates costs across patients"""
    
    def __init__(self, analyzer: CostAnalyzer):
        self.analyzer = analyzer
        self.cost_events: List[CostEvent] = []
        
    def process_simulation_results(self, results: Dict[str, Any]) -> None:
        """Process simulation results and extract all costs"""
        
        patient_histories = results.get('patient_histories', {})
        
        for patient_id, history in patient_histories.items():
            events = self.analyzer.analyze_patient_history(history)
            self.cost_events.extend(events)
            
    def get_patient_costs(self, patient_id: str) -> pd.DataFrame:
        """Get all costs for a specific patient"""
        
        patient_events = [e for e in self.cost_events if e.patient_id == patient_id]
        
        if not patient_events:
            return pd.DataFrame()
            
        return pd.DataFrame([
            {
                'time': e.time,
                'event_type': e.event_type,
                'category': e.category,
                'amount': e.amount,
                'drug_cost': e.metadata.get('drug_cost', 0),
                'visit_cost': e.metadata.get('visit_cost', 0),
                'phase': e.metadata.get('phase', 'unknown')
            }
            for e in patient_events
        ])
        
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics across all patients"""
        
        if not self.cost_events:
            return {}
            
        df = pd.DataFrame([
            {
                'patient_id': e.patient_id,
                'time': e.time,
                'amount': e.amount,
                'event_type': e.event_type,
                'category': e.category
            }
            for e in self.cost_events
        ])
        
        return {
            'total_patients': df['patient_id'].nunique(),
            'total_cost': df['amount'].sum(),
            'avg_cost_per_patient': df.groupby('patient_id')['amount'].sum().mean(),
            'cost_by_type': df.groupby('event_type')['amount'].sum().to_dict(),
            'cost_by_category': df.groupby('category')['amount'].sum().to_dict()
        }
        
    def export_to_parquet(self, output_path: Path) -> None:
        """Export cost data to Parquet for Streamlit"""
        
        if not self.cost_events:
            return
            
        # Create detailed event dataframe
        events_df = pd.DataFrame([
            {
                'patient_id': e.patient_id,
                'time': e.time,
                'event_type': e.event_type,
                'category': e.category,
                'amount': e.amount,
                'drug_cost': e.metadata.get('drug_cost', 0),
                'visit_cost': e.metadata.get('visit_cost', 0),
                'phase': e.metadata.get('phase', 'unknown'),
                **{f'component_{k}': v for k, v in e.components.items()}
            }
            for e in self.cost_events
        ])
        
        # Save events
        events_df.to_parquet(output_path / 'cost_events.parquet')
        
        # Create and save patient summary
        patient_summary = events_df.groupby('patient_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'drug_cost': 'sum',
            'visit_cost': 'sum'
        }).reset_index()
        
        patient_summary.columns = ['patient_id', 'total_cost', 'avg_cost_per_event', 
                                   'num_events', 'total_drug_cost', 'total_visit_cost']
        patient_summary.to_parquet(output_path / 'cost_summary.parquet')
```

### 1.4 Integration Script

**File: `run_simulation_with_costs.py`**
```python
#!/usr/bin/env python3
"""
Run simulation with cost tracking
"""

from pathlib import Path
from simulation.economics import CostConfig, CostAnalyzer, CostTracker
from run_simulation import run_simulation  # Existing simulation runner

def main():
    # Run clinical simulation (existing code)
    clinical_results = run_simulation(
        protocol_file="protocols/eylea.yaml",
        num_patients=100,
        simulation_years=3
    )
    
    # Load cost configuration
    cost_config = CostConfig.from_yaml(
        Path("protocols/cost_configs/nhs_standard_2025.yaml")
    )
    
    # Analyze costs
    analyzer = CostAnalyzer(cost_config)
    tracker = CostTracker(analyzer)
    
    # Process simulation results
    tracker.process_simulation_results(clinical_results)
    
    # Print summary
    summary = tracker.get_summary_statistics()
    print("\n=== Cost Analysis Summary ===")
    print(f"Total patients: {summary['total_patients']}")
    print(f"Total cost: £{summary['total_cost']:,.2f}")
    print(f"Average cost per patient: £{summary['avg_cost_per_patient']:,.2f}")
    
    # Export for Streamlit
    output_dir = Path("output/simulation_results/costs")
    output_dir.mkdir(parents=True, exist_ok=True)
    tracker.export_to_parquet(output_dir)
    
    print(f"\nCost data exported to {output_dir}")

if __name__ == "__main__":
    main()
```

## Phase 2: Enhanced Visit Metadata (Week 2) ✅ COMPLETED

### Phase 2.5: V2 Financial System Modernization 🔄 IN PROGRESS

**IMPORTANT**: Before proceeding to Phase 3, we need to modernize the financial system to work natively with simulation_v2. See [FINANCIAL_V2_IMPLEMENTATION_PLAN.md](FINANCIAL_V2_IMPLEMENTATION_PLAN.md) for the complete 5-day implementation plan.

This modernization will:
- Remove all V1 compatibility requirements
- Create native V2 data format support
- Implement Option A (Extend V2 Patient Class) for visit enhancement
- Provide a clean API for economic integration
- Enable seamless cost tracking without data conversion

Once this modernization is complete, Phase 3 visualization integration will be much simpler.

### 2.1 Modify Visit Creation

**Update existing visit creation to add metadata:**

```python
# In simulation/base.py or wherever visits are created

def create_visit(visit_type: str, time: float, patient_state: Any, **kwargs) -> Dict:
    """Enhanced visit creation with cost metadata"""
    
    visit = {
        'type': visit_type,
        'time': time,
        # ... existing fields ...
    }
    
    # Add cost-relevant metadata
    visit['metadata'] = {
        'phase': patient_state.phase,  # 'loading', 'maintenance', etc.
        'visit_number': patient_state.visit_count,
        'days_since_last': time - patient_state.last_visit_time if patient_state.last_visit_time else 0
    }
    
    # Protocol-specific metadata
    if visit_type == 'injection' and patient_state.phase == 'loading':
        visit['metadata']['visit_subtype'] = 'injection_loading'
        visit['metadata']['components_performed'] = ['injection', 'visual_acuity_test']
    
    return visit
```

### 2.2 Test-Implementation Mapping

| Test File | Implementation File | Purpose |
|-----------|-------------------|----------|
| `test_cost_config.py` | `cost_config.py` | Configuration loading and cost calculations |
| `test_cost_analyzer.py` | `cost_analyzer.py` | Visit analysis and component inference |
| `test_cost_tracker.py` | `cost_tracker.py` | Patient history processing and aggregation |
| `test_economic_integration.py` | All files | End-to-end validation |

### 2.3 Example Test Implementation

**File: `tests/unit/test_cost_config.py`**
```python
import pytest
from pathlib import Path
from simulation.economics import CostConfig

class TestCostConfig:
    """Test suite for CostConfig class - following TDD approach"""
    
    def test_load_cost_config_from_yaml(self):
        """Test 1.1: Load basic cost configuration"""
        # This test will fail initially (Red phase)
        config_path = Path("tests/fixtures/economics/test_cost_config.yaml")
        config = CostConfig.from_yaml(config_path)
        
        assert config.metadata['name'] == "Test Cost Configuration"
        assert config.metadata['currency'] == "GBP"
        assert 'test_drug' in config.drug_costs
        
    def test_get_drug_cost(self):
        """Test 1.2: Access drug costs"""
        config = self._get_test_config()
        
        assert config.get_drug_cost('test_drug') == 100.0
        assert config.get_drug_cost('unknown_drug') == 0.0  # Safe default
        
    def test_calculate_visit_cost_from_components(self):
        """Test 1.3: Calculate visit costs from components"""
        config = self._get_test_config()
        
        # injection (50) + oct_scan (25) = 75
        assert config.get_visit_cost('test_visit') == 75.0
        
    def test_visit_cost_with_override(self):
        """Test 1.4: Handle cost overrides"""
        config = self._get_test_config()
        # Add test for override functionality
        pass  # Implementation pending
```

### 2.4 Validation Test Example

**File: `tests/unit/test_cost_analyzer.py`**
```python
import pytest
from pathlib import Path
from simulation.economics import CostConfig, CostAnalyzer

def test_basic_visit_costing():
    """Test basic visit cost calculation"""
    
    # Load test config
    config = CostConfig.from_yaml(
        Path("protocols/cost_configs/nhs_standard_2025_test.yaml")
    )
    analyzer = CostAnalyzer(config)
    
    # Test injection visit with metadata
    visit = {
        'type': 'injection',
        'time': 0,
        'drug': 'eylea_2mg',
        'metadata': {
            'visit_subtype': 'injection_virtual',
            'phase': 'maintenance'
        }
    }
    
    cost_event = analyzer.analyze_visit(visit)
    
    assert cost_event is not None
    assert cost_event.amount == 1085  # 800 drug + 285 visit
    assert cost_event.metadata['drug_cost'] == 800
    assert cost_event.metadata['visit_cost'] == 285

def test_component_inference():
    """Test component inference when metadata is missing"""
    
    config = CostConfig.from_yaml(
        Path("protocols/cost_configs/nhs_standard_2025_test.yaml")
    )
    analyzer = CostAnalyzer(config)
    
    # Visit without detailed metadata
    visit = {
        'type': 'injection',
        'time': 0,
        'metadata': {
            'phase': 'loading'
        }
    }
    
    components = analyzer._determine_components(visit)
    
    assert 'injection' in components
    assert 'visual_acuity_test' in components
    assert len(components) == 2  # Loading phase is simpler
```

## Phase 3: Visualization Integration (Week 3)

### 3.1 Cost Visualization Module

**File: `visualization/cost_viz.py`**
```python
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def create_cost_accumulation_plot(cost_events_df: pd.DataFrame, patient_id: str = None):
    """Create cumulative cost plot over time"""
    
    if patient_id:
        df = cost_events_df[cost_events_df['patient_id'] == patient_id].copy()
        title = f"Cost Accumulation - Patient {patient_id}"
    else:
        # Aggregate across all patients
        df = cost_events_df.groupby('time')['amount'].sum().reset_index()
        title = "Total Cost Accumulation - All Patients"
    
    df['cumulative_cost'] = df['amount'].cumsum()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['time'], df['cumulative_cost'], linewidth=2)
    ax.set_xlabel('Time (months)')
    ax.set_ylabel('Cumulative Cost (£)')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    return fig

def create_cost_breakdown_chart(summary_stats: Dict[str, Any]):
    """Create cost breakdown pie chart"""
    
    cost_by_category = summary_stats['cost_by_category']
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(cost_by_category.values(), 
           labels=cost_by_category.keys(),
           autopct='%1.1f%%')
    ax.set_title('Cost Breakdown by Category')
    
    return fig
```

## Next Steps After Phase 1

1. **Validate with test data** - Ensure cost calculations match expected NHS tariffs
2. **Add special events** - Implement discontinuation costs, adverse events
3. **Enhance inference rules** - Improve component detection for edge cases
4. **Create Streamlit pages** - Add cost analysis tab to existing app
5. **Protocol comparison** - Build tools to compare costs across protocols

## Success Criteria

Phase 1 (Core Infrastructure):
- [ ] All CostConfig tests pass (4 tests)
- [ ] All CostAnalyzer tests pass (4 tests)
- [ ] All CostTracker tests pass (4 tests)
- [ ] Integration tests pass (2 tests)
- [ ] Code coverage > 90% for economics module

Phase 2 (Integration):
- [ ] Cost config loads from YAML successfully
- [ ] Basic visit costs calculate correctly
- [ ] Integration doesn't break existing simulation
- [ ] Parquet export works for Streamlit
- [ ] Summary statistics match manual calculations

Phase 3 (Validation):
- [ ] Cost calculations verified against NHS tariffs
- [ ] Performance benchmarks met (< 1s for 1000 patients)
- [ ] Documentation complete

## Risk Mitigation

1. **Backward compatibility** - All cost features are additive, no breaking changes
2. **Performance** - Cost calculation is post-processing, doesn't slow simulation
3. **Validation** - Extensive unit tests before integration
4. **Gradual rollout** - Can enable/disable cost tracking via configuration