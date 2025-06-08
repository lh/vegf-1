# V2 Economics Integration Usage Guide

## Overview

The V2 Economics Integration provides a simple, powerful API for adding economic analysis to AMD simulations. With just 1-3 lines of code, you can add comprehensive cost tracking and financial analysis to any V2 simulation.

## Quick Start

### Method 1: All-in-One Simulation with Economics

The simplest way to run a simulation with economics:

```python
from simulation_v2.economics import EconomicsIntegration, CostConfig
from simulation_v2.protocols.protocol_spec import ProtocolSpecification

# Load configurations
protocol = ProtocolSpecification.from_yaml("protocols/eylea.yaml")
costs = CostConfig.from_yaml("costs/nhs_standard.yaml")

# Run simulation with economics in one line
clinical, financial = EconomicsIntegration.run_with_economics(
    'abs',                    # Engine type: 'abs' or 'des'
    protocol,                 # Protocol specification
    costs,                    # Cost configuration
    n_patients=100,           # Number of patients
    duration_years=2.0,       # Simulation duration
    seed=42                   # Random seed
)

# Results are immediately available
print(f"Cost per patient: £{financial.cost_per_patient:,.2f}")
print(f"Cost per letter gained: £{financial.cost_per_letter_gained:,.2f}")
```

### Method 2: Engine Creation from Files

Create an engine with economics from configuration files:

```python
# Create engine directly from YAML files
engine = EconomicsIntegration.create_from_files(
    'abs',
    'protocols/eylea.yaml',
    'costs/nhs_standard.yaml',
    n_patients=100
)

# Run simulation
results = engine.run(duration_years=2.0)

# Analyze costs separately
financial = EconomicsIntegration.analyze_results(results, costs)
```

### Method 3: Manual Engine Creation

For more control over the process:

```python
# Create enhanced engine with full control
engine = EconomicsIntegration.create_enhanced_engine(
    'des',
    protocol_spec=protocol,
    cost_config=costs,
    n_patients=50,
    seed=123,
    max_queue_size=1000  # Engine-specific parameters
)

results = engine.run(duration_years=3.0)
financial = EconomicsIntegration.analyze_results(results, costs)
```

## Cost Configuration

### Creating Cost Configurations

Cost configurations are defined in YAML files:

```yaml
metadata:
  name: "NHS Standard Costs 2025"
  currency: "GBP"
  effective_date: "2025-01-01"

drug_costs:
  eylea_2mg: 800.00
  eylea_8mg: 1200.00
  avastin: 50.00
  lucentis: 650.00

visit_components:
  vision_test: 25.00
  oct_scan: 150.00
  injection: 100.00
  pressure_check: 20.00
  virtual_review: 50.00
  face_to_face_review: 120.00

visit_types:
  loading_injection_visit:
    components: [vision_test, oct_scan, injection]
    # Total cost = 25 + 150 + 100 = 275 (plus drug cost)
  
  maintenance_monitoring_visit:
    components: [vision_test, oct_scan, virtual_review]
    # Total cost = 25 + 150 + 50 = 225
  
  initial_assessment:
    total_override: 350.00  # Override component calculation

special_events:
  discontinuation_admin: 50.00
  adverse_event_assessment: 200.00
```

### Loading Cost Configurations

```python
from simulation_v2.economics import CostConfig

# Load from YAML file
costs = CostConfig.from_yaml("costs/nhs_standard.yaml")

# Access cost information
drug_cost = costs.get_drug_cost('eylea_2mg')  # 800.00
visit_cost = costs.get_visit_cost('loading_injection_visit')  # 275.00
component_cost = costs.get_component_cost('oct_scan')  # 150.00
```

## Financial Results

The `FinancialResults` object provides comprehensive cost analysis:

```python
# After running simulation with economics
clinical, financial = EconomicsIntegration.run_with_economics(...)

# Summary metrics
print(f"Total cost: £{financial.total_cost:,.2f}")
print(f"Total patients: {financial.total_patients}")
print(f"Cost per patient: £{financial.cost_per_patient:,.2f}")
print(f"Total injections: {financial.total_injections}")
print(f"Cost per injection: £{financial.cost_per_injection:,.2f}")

# Cost-effectiveness
if financial.cost_per_letter_gained:
    print(f"Cost per letter gained: £{financial.cost_per_letter_gained:,.2f}")

# Detailed breakdowns
breakdown = financial.cost_breakdown

# By event type
print("Costs by type:")
for event_type, cost in breakdown.by_type.items():
    print(f"  {event_type}: £{cost:,.2f}")

# By treatment phase
print("Costs by phase:")
for phase, cost in breakdown.by_phase.items():
    print(f"  {phase}: £{cost:,.2f}")

# By visit category
print("Costs by category:")
for category, cost in breakdown.by_category.items():
    print(f"  {category}: £{cost:,.2f}")

# Individual patient costs
for patient_id, patient_cost in financial.patient_costs.items():
    print(f"Patient {patient_id}:")
    print(f"  Total: £{patient_cost.total_cost:,.2f}")
    print(f"  Injections: {patient_cost.injection_count}")
    print(f"  Cost per injection: £{patient_cost.cost_per_injection:,.2f}")
```

## Exporting Results

The EconomicsIntegration API provides easy export functionality:

```python
# Run simulation
clinical, financial = EconomicsIntegration.run_with_economics(...)

# Export results in multiple formats
EconomicsIntegration.export_results(
    financial, 
    output_dir="output/my_analysis",
    formats=['json', 'csv', 'parquet']
)

# Files created:
# - output/my_analysis/financial_summary.json
# - output/my_analysis/financial_summary.csv
# - output/my_analysis/patient_costs.parquet
# - output/my_analysis/cost_events.parquet
```

## Protocol Comparison

Compare multiple protocols economically:

```python
from pathlib import Path

protocols = [
    'protocols/eylea_monthly.yaml',
    'protocols/eylea_treat_extend.yaml',
    'protocols/faricimab_q8.yaml'
]

results = {}
for protocol_path in protocols:
    protocol = ProtocolSpecification.from_yaml(protocol_path)
    
    # Run both ABS and DES for each protocol
    for engine_type in ['abs', 'des']:
        clinical, financial = EconomicsIntegration.run_with_economics(
            engine_type, protocol, costs, 100, 2.0
        )
        
        key = f"{protocol.name}_{engine_type}"
        results[key] = {
            'clinical': clinical,
            'financial': financial
        }

# Analyze results
for key, data in results.items():
    print(f"{key}:")
    print(f"  Cost per patient: £{data['financial'].cost_per_patient:,.2f}")
    print(f"  Cost per letter: £{data['financial'].cost_per_letter_gained:,.2f}")
```

## Advanced Usage

### Custom Cost Enhancement

For specialized cost tracking, you can create custom enhancers:

```python
from simulation_v2.economics import create_v2_cost_enhancer

def custom_enhancer(visit, patient):
    """Custom cost enhancement function."""
    # Apply standard enhancement first
    standard_enhancer = create_v2_cost_enhancer(cost_config, "eylea")
    enhanced_visit = standard_enhancer(visit, patient)
    
    # Add custom logic
    metadata = enhanced_visit['metadata']
    
    # Example: Add complexity scoring
    if patient.age > 80:
        metadata['complexity_multiplier'] = 1.2
    
    if len(patient.comorbidities) > 2:
        metadata['components_performed'].append('extended_consultation')
    
    return enhanced_visit

# Use custom enhancer
engine = EconomicsIntegration.create_enhanced_engine(
    'abs', protocol, costs, 100,
    visit_metadata_enhancer=custom_enhancer
)
```

### Batch Analysis

Process multiple simulations efficiently:

```python
def analyze_parameter_sensitivity():
    """Analyze cost sensitivity to different parameters."""
    
    base_protocol = ProtocolSpecification.from_yaml("protocols/eylea.yaml")
    costs = CostConfig.from_yaml("costs/nhs_standard.yaml")
    
    # Test different patient cohort sizes
    cohort_sizes = [50, 100, 200, 500]
    duration_years = 2.0
    
    results = []
    
    for n_patients in cohort_sizes:
        clinical, financial = EconomicsIntegration.run_with_economics(
            'abs', base_protocol, costs, n_patients, duration_years
        )
        
        results.append({
            'n_patients': n_patients,
            'total_cost': financial.total_cost,
            'cost_per_patient': financial.cost_per_patient,
            'cost_per_injection': financial.cost_per_injection,
            'cost_per_letter': financial.cost_per_letter_gained
        })
    
    return results
```

## Performance Considerations

### Memory Management

For large simulations (>1000 patients), consider:

```python
# Use DES for better memory efficiency with large cohorts
clinical, financial = EconomicsIntegration.run_with_economics(
    'des',  # Better for large cohorts
    protocol, costs, 
    n_patients=5000,
    duration_years=5.0
)

# Export large results to Parquet for efficient storage
EconomicsIntegration.export_results(
    financial, 
    "output/large_simulation",
    formats=['parquet']  # Most efficient format
)
```

### Parallel Processing

For multiple simulations:

```python
from concurrent.futures import ProcessPoolExecutor

def run_single_simulation(params):
    protocol, costs, n_patients, seed = params
    return EconomicsIntegration.run_with_economics(
        'abs', protocol, costs, n_patients, 2.0, seed
    )

# Run multiple simulations in parallel
simulation_params = [
    (protocol, costs, 100, seed) 
    for seed in range(10)  # 10 replications
]

with ProcessPoolExecutor() as executor:
    all_results = list(executor.map(run_single_simulation, simulation_params))

# Aggregate results
total_costs = [result[1].total_cost for result in all_results]
mean_cost = sum(total_costs) / len(total_costs)
```

## Troubleshooting

### Common Issues

1. **Missing Protocol Files**
   ```python
   # Check if files exist before loading
   from pathlib import Path
   
   protocol_path = Path("protocols/eylea.yaml")
   if not protocol_path.exists():
       raise FileNotFoundError(f"Protocol file not found: {protocol_path}")
   ```

2. **Invalid Cost Configuration**
   ```python
   # Validate cost config after loading
   costs = CostConfig.from_yaml("costs/nhs_standard.yaml")
   
   # Check required components exist
   required_components = ['vision_test', 'oct_scan', 'injection']
   missing = [c for c in required_components if costs.get_component_cost(c) == 0]
   if missing:
       print(f"Warning: Missing costs for components: {missing}")
   ```

3. **Zero or Negative Costs**
   ```python
   # Check for reasonable cost values
   if financial.cost_per_patient <= 0:
       print("Warning: Zero or negative cost per patient")
       print("Check cost configuration and visit enhancement")
   ```

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Economics operations will now log detailed information
clinical, financial = EconomicsIntegration.run_with_economics(...)
```

Inspect cost events:

```python
# Create tracker to examine individual cost events
from simulation_v2.economics import CostAnalyzerV2, CostTrackerV2

analyzer = CostAnalyzerV2(costs)
tracker = CostTrackerV2(analyzer)
tracker.process_v2_results(clinical)

# Examine events for specific patients
patient_events = tracker.events['P001']
for event in patient_events:
    print(f"Date: {event.date}, Type: {event.event_type}, Amount: £{event.amount}")
```

## Best Practices

1. **Use Real Protocol Files**: Always use actual protocol YAML files rather than manually creating specifications

2. **Validate Configurations**: Check that cost configurations include all required components

3. **Set Random Seeds**: Use consistent seeds for reproducible results

4. **Export Results**: Always export detailed results for later analysis

5. **Test Both Engines**: Compare ABS and DES results to understand engine differences

6. **Monitor Performance**: Use appropriate engines for your cohort size (ABS for small, DES for large)

7. **Version Control**: Track protocol and cost configuration versions in your analysis

## Migration from V1

If you're migrating from V1 economics code:

### Before (V1 - Complex)
```python
# 50+ lines of manual setup
from simulation.economics import CostAnalyzer, CostTracker, SimulationCostAdapter
# ... manual engine creation ...
# ... manual data conversion ...
# ... manual cost analysis ...
```

### After (V2 - Simple)
```python
# 3 lines total
clinical, financial = EconomicsIntegration.run_with_economics(
    'abs', protocol, costs, 100, 2.0
)
```

The new API provides identical functionality with 95% less code and better performance.

## API Reference

### EconomicsIntegration Methods

- `run_with_economics()`: All-in-one simulation with economics
- `create_enhanced_engine()`: Create engine with cost tracking
- `create_from_files()`: Create engine from configuration files
- `analyze_results()`: Analyze existing simulation results
- `export_results()`: Export results in multiple formats

### CostConfig Methods

- `from_yaml()`: Load configuration from YAML file
- `get_drug_cost()`: Get cost for specific drug
- `get_visit_cost()`: Calculate total visit cost
- `get_component_cost()`: Get cost for visit component
- `get_special_event_cost()`: Get cost for special events

### FinancialResults Properties

- `total_cost`: Total simulation cost
- `cost_per_patient`: Average cost per patient
- `cost_per_injection`: Average cost per injection
- `cost_per_letter_gained`: Cost-effectiveness metric
- `cost_breakdown`: Detailed cost breakdowns
- `patient_costs`: Individual patient cost summaries
- `monthly_costs`: Time series of monthly costs
- `cumulative_costs`: Cumulative cost progression

This guide covers the essential usage patterns for V2 economics integration. The API is designed to be simple, powerful, and efficient for both simple analyses and complex economic studies.