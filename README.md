# APE: AMD Protocol Explorer

This repository contains the codebase for simulating, analyzing, and visualizing AMD treatment protocols, with a focus on VEGF inhibitors like Eylea. The project includes tools for modeling disease progression, analyzing treatment outcomes, and visualizing results through both command line tools and an interactive Streamlit dashboard.

## Features

- **Simulation Models**: Agent-based and discrete event simulations for disease progression and treatment effects.
- **Parameter Configurations**: YAML-based configuration files for flexible protocol definitions.
- **Data Analysis**: Tools for analyzing injection intervals, visual acuity changes, and treatment persistence.
- **Visualization**: Generate heatmaps, waterfall plots, and other visualizations for treatment patterns with a consistent Tufte-inspired visual grammar.
- **Interactive Dashboard**: Streamlit-based interface for running simulations and exploring results.
- **Report Generation**: Create comprehensive reports with Quarto integration.

## Documentation

Comprehensive documentation for the project is available. To view it, click the link below:

[View Documentation](https://lh.github.io/vegf-1/)


The documentation includes:
- Setup instructions
- Detailed descriptions of simulation models
- Examples of configuration files
- Analysis and visualization guides

## Repository Structure

```
├── protocols/                # Configuration files for simulations
│   ├── parameter_sets/       # Parameter sets for different protocols
│   └── simulation_configs/   # Simulation configuration files
├── simulation/               # Core simulation models and logic
├── validation/               # Configuration validation tools
├── visualization/            # Visualization scripts and templates
│   ├── color_system.py      # Centralized color palette
│   ├── visualization_templates.py  # Standardized chart templates
│   └── acuity_viz.py        # Visual acuity visualization functions
├── streamlit_app/            # Interactive Streamlit dashboard
│   ├── app.py                # Main Streamlit application
│   ├── amd_protocol_explorer.py  # Dashboard implementation
│   ├── simulation_runner.py  # Simulation execution
│   ├── quarto_utils.py       # Quarto integration
│   ├── assets/               # Dashboard assets
│   └── reports/              # Quarto report templates
├── tests/                    # Unit tests for the project
├── docs/                     # Sphinx documentation source
├── run_ape.py                # Entry point for the Streamlit app
└── setup_streamlit.py        # Setup script for the Streamlit environment
```

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ape.git
   cd ape
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run a sample simulation from the command line:
   ```bash
   python run_eylea_analysis.py --config protocols/simulation_configs/test_simulation.yaml --output output/
   ```

4. View the results in the `output/` directory.

### Running the Dashboard

1. Install Streamlit dependencies:
   ```bash
   pip install -r streamlit_requirements.txt
   ```

2. Setup the Streamlit environment:
   ```bash
   python setup_streamlit.py
   ```

3. Run the dashboard:
   ```bash
   python run_ape.py
   ```

4. Access the dashboard in your browser at http://localhost:8502

## Visualization System

The project includes a comprehensive visualization system that follows Edward Tufte's design principles:

1. **Consistent Color System**:
   - Steel Blue (`#4682B4`) for visual acuity data
   - Sage Green (`#8FAD91`) for patient counts
   - Firebrick Red (`#B22222`) for critical information

2. **Standardized Templates**:
   - `patient_time` - Visual acuity by patient time with sample counts
   - `enrollment_chart` - Patient enrollment over time
   - `acuity_time_series` - Visual acuity time series
   - `protocol_comparison` - Treatment protocol comparison

3. **Usage**:
   ```python
   from visualization.visualization_templates import create_patient_time_visualization

   fig, ax = create_patient_time_visualization(
       data,
       time_col='weeks_since_enrollment',
       acuity_col='etdrs_letters',
       title='Visual Acuity Over Time'
   )
   ```

For more details, see the [Visualization README](visualization/README.md).

## V2 Economics Integration

The project includes a powerful economics module that enables comprehensive cost analysis of AMD treatment protocols with minimal code.

### Quick Start with Economics

Add economic analysis to any simulation with just one line:

```python
from simulation_v2.economics import EconomicsIntegration, CostConfig
from simulation_v2.protocols.protocol_spec import ProtocolSpecification

# Load configurations
protocol = ProtocolSpecification.from_yaml("protocols/eylea.yaml")
costs = CostConfig.from_yaml("costs/nhs_standard.yaml")

# Run simulation with economics - ONE LINE!
clinical, financial = EconomicsIntegration.run_with_economics(
    'abs', protocol, costs, n_patients=100, duration_years=2.0, seed=42
)

# Results immediately available
print(f"Cost per patient: £{financial.cost_per_patient:,.2f}")
print(f"Cost per letter gained: £{financial.cost_per_letter_gained:,.2f}")
print(f"Total injections: {financial.total_injections}")
```

### Key Features

- **One-Line Integration**: Add economics to any simulation with a single method call
- **Comprehensive Analysis**: Automatic calculation of cost per patient, per injection, and per letter gained
- **Flexible Configuration**: YAML-based cost configurations for different healthcare systems
- **Rich Results**: Detailed breakdowns by treatment phase, visit type, and patient
- **Multiple Formats**: Export results as JSON, CSV, or Parquet
- **Protocol Comparison**: Easy comparison of economic outcomes across protocols

### Cost Configuration

Define costs in YAML format:

```yaml
metadata:
  name: "NHS Standard Costs 2025"
  currency: "GBP"

drug_costs:
  eylea_2mg: 800.00
  eylea_8mg: 1200.00
  avastin: 50.00

visit_components:
  vision_test: 25.00
  oct_scan: 150.00
  injection: 100.00
  virtual_review: 50.00

visit_types:
  loading_injection_visit:
    components: [vision_test, oct_scan, injection]
  maintenance_monitoring_visit:
    components: [vision_test, oct_scan, virtual_review]

special_events:
  discontinuation_admin: 50.00
```

### Protocol Comparison Example

```python
# Compare multiple protocols economically
protocols = ['eylea_monthly.yaml', 'eylea_treat_extend.yaml', 'faricimab_q8.yaml']
costs = CostConfig.from_yaml("costs/nhs_standard.yaml")

results = {}
for protocol_file in protocols:
    protocol = ProtocolSpecification.from_yaml(f"protocols/{protocol_file}")
    
    clinical, financial = EconomicsIntegration.run_with_economics(
        'abs', protocol, costs, 100, 2.0
    )
    
    results[protocol.name] = {
        'cost_per_patient': financial.cost_per_patient,
        'cost_per_injection': financial.cost_per_injection,
        'cost_per_letter': financial.cost_per_letter_gained
    }

# Create comparison visualization
EconomicsIntegration.create_comparison_chart(results, "output/protocol_comparison.png")
```

### Advanced Usage

For specialized analysis, create custom cost enhancers:

```python
# Custom cost enhancement for research studies
def research_enhancer(visit, patient):
    standard_enhancer = create_v2_cost_enhancer(cost_config, "eylea")
    enhanced_visit = standard_enhancer(visit, patient)
    
    # Add research-specific costs
    metadata = enhanced_visit['metadata']
    if patient.age > 80:
        metadata['components_performed'].append('extended_consultation')
    
    return enhanced_visit

# Use with EconomicsIntegration
engine = EconomicsIntegration.create_enhanced_engine(
    'abs', protocol, costs, 100,
    visit_metadata_enhancer=research_enhancer
)
```

### Performance and Scalability

The V2 economics system is optimized for performance:

- **ABS Engine**: Ideal for small-medium cohorts (≤1000 patients)
- **DES Engine**: Optimized for large cohorts (>1000 patients)
- **Memory Efficient**: No data duplication between clinical and economic analysis
- **Parallel Processing**: Built-in support for concurrent simulations

### Documentation

- [V2 Economics Usage Guide](docs/V2_ECONOMICS_USAGE_GUIDE.md) - Comprehensive usage examples
- [V1 to V2 Migration Guide](docs/V1_TO_V2_MIGRATION_GUIDE.md) - Migrate from legacy economics code
- [API Reference](simulation_v2/economics/README.md) - Detailed API documentation

### Example Scripts

- `run_v2_simulation_with_economics.py` - Simple economics demonstration
- `compare_protocols_with_economics.py` - Multi-protocol economic comparison
- `examples/cost_tracking_example.py` - Advanced cost tracking patterns

### Testing

Run the comprehensive economics test suite:

```bash
pytest tests/test_v2_economics_integration.py -v
```

The test suite covers:
- ✅ Cost configuration loading and validation
- ✅ Visit enhancement and metadata generation
- ✅ Financial analysis and calculations
- ✅ EconomicsIntegration API functionality
- ✅ Edge cases and error handling

### Migration from V1

If you're using the legacy V1 economics system:

**Before (V1 - Complex)**:
```python
# 50+ lines of manual setup, data conversion, and analysis
from simulation.economics import CostAnalyzer, CostTracker, SimulationCostAdapter
# ... extensive manual configuration ...
```

**After (V2 - Simple)**:
```python
# 3 lines total with better functionality
clinical, financial = EconomicsIntegration.run_with_economics(
    'abs', protocol, costs, 100, 2.0
)
```

See the [Migration Guide](docs/V1_TO_V2_MIGRATION_GUIDE.md) for complete migration instructions.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
