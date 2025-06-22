# Cost Tracking Implementation Plan

## Overview
This document outlines the plan for implementing comprehensive cost tracking in the VEGF simulation, including drug costs, visit costs, workload metrics, and cost-effectiveness analysis.

## 1. Cost Components to Track

### 1.1 Drug Costs
- **Eylea (Aflibercept) 2mg**: Default NHS price £800 (adjustable via slider)
- **Future support**: Other anti-VEGF drugs (Lucentis, Avastin, Vabysmo, Eylea HD)

### 1.2 Visit Types and Costs

#### Injection-Only Visit
- **Components**: Injection administration + basic checks
- **Cost**: £150 (injection) + £10 (pressure check) = £160
- **Workload**: 1 injection, 0 decision-maker interventions

#### Full Decision-Making Visit (T&E)
- **Components**: OCT scan + visual acuity test + clinical review + injection (if needed)
- **Cost**: £75 (OCT) + £25 (VA test) + £120 (F2F review) + £150 (injection if given) = £220-370
- **Workload**: 0-1 injection, 1 decision-maker intervention

#### Monitoring Visit (no injection)
- **Components**: OCT scan + visual acuity test + clinical review
- **Cost**: £75 (OCT) + £25 (VA test) + £120 (F2F review) = £220
- **Workload**: 0 injections, 1 decision-maker intervention

### 1.3 Special Events
- **Initial assessment**: £250
- **Discontinuation administration**: £50
- **Adverse event management**: £500-2000

## 2. Data Sources and References

### Existing Repository Data
1. **NHS Standard Costs**: `/protocols/cost_configs/nhs_standard_2025.yaml`
2. **Cost Calculator Analysis**: `/workspace/cost_calculator_protocols_summary.md`
3. **Economics Module**: `/simulation_v2/economics/` (existing framework)

### Key Cost Parameters (from NHS data)
```yaml
# Core costs
drug_cost_eylea_2mg: 800  # GBP per dose
injection_procedure: 150  # HRG BZ86B equivalent
oct_scan: 75             # HRG BZ88A equivalent
clinical_review_f2f: 120 # Face-to-face review
clinical_review_virtual: 50  # Virtual review
visual_acuity_test: 25
```

## 3. Implementation Architecture

### 3.1 Cost Configuration Enhancement
```python
# Enhanced cost_config.py structure
class CostConfig:
    def __init__(self):
        self.drug_costs = {
            'eylea_2mg': 800,  # Default, adjustable
            'eylea_8mg': 1197.60,
            'lucentis': 613.20,
            'avastin': 50
        }
        
        self.visit_costs = {
            'injection_only': {
                'components': ['injection', 'pressure_check'],
                'decision_maker': False
            },
            'full_assessment': {
                'components': ['oct_scan', 'va_test', 'clinical_review', 'injection'],
                'decision_maker': True
            },
            'monitoring_only': {
                'components': ['oct_scan', 'va_test', 'clinical_review'],
                'decision_maker': True
            }
        }
```

### 3.2 Enhanced Cost Tracker
```python
class EnhancedCostTracker:
    def track_visit(self, patient_id, visit_date, visit_type):
        """Track costs and workload for a visit"""
        # Record drug cost if injection given
        # Record visit component costs
        # Track workload metrics:
        #   - injection_count
        #   - decision_maker_count
        
    def get_workload_timeline(self):
        """Return timeline of injections and decision-maker interventions"""
        
    def get_cost_effectiveness(self):
        """Calculate cost per vision saved"""
```

### 3.3 Protocol Integration

#### For T&E Protocols
- Loading phase: Full assessment visits
- Maintenance: Full assessment at each visit (decision + possible injection)
- Track interval changes as workload indicator

#### For T&T (Fixed) Protocols
- Loading phase: Injection-only visits (except first/last)
- Maintenance: Mostly injection-only visits
- Quarterly full assessments for safety monitoring

## 4. User Interface Components

### 4.1 Cost Configuration Widget
```python
# In Streamlit UI
st.sidebar.subheader("Cost Parameters")

# Drug cost slider
eylea_cost = st.sidebar.slider(
    "Eylea 2mg cost (£)",
    min_value=400,
    max_value=1200,
    value=800,
    step=50,
    help="NHS list price is £800. Adjust for local contracts or biosimilars."
)

# Visit cost options
visit_cost_model = st.sidebar.selectbox(
    "Visit cost model",
    ["NHS Standard 2025", "Custom", "Minimal (injection only)"]
)
```

### 4.2 Workload Visualization
1. **Timeline Chart**: Stacked area showing injections vs decision-maker visits over time
2. **Resource Utilization**: Monthly/quarterly workload summaries
3. **Cost Breakdown**: Pie chart of drug vs visit costs

### 4.3 Cost-Effectiveness Dashboard
- Total cost per patient
- Cost per vision year saved
- Budget impact for different patient populations
- Comparison between T&E and T&T strategies

## 5. Analysis and Metrics

### 5.1 Primary Metrics
1. **Total Cost per Patient**: Drug + visit costs over simulation period
2. **Workload Metrics**:
   - Total injections administered
   - Total decision-maker interventions
   - Peak monthly workload
3. **Cost-Effectiveness**:
   - Cost per letter of vision gained
   - Cost per patient maintaining driving vision (>70 letters)
   - QALY calculations (if utility data available)

### 5.2 Comparative Analysis
- T&E vs T&T cost differential
- Impact of drug price changes
- Workload implications of different protocols
- Budget impact modeling

## 6. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Enhance CostConfig with visit types
- [ ] Add workload tracking to CostTracker
- [ ] Create cost parameter YAML files

### Phase 2: Protocol Integration (Week 2)
- [ ] Modify visit logic to track visit types
- [ ] Implement T&E vs T&T visit patterns
- [ ] Add decision-maker tracking

### Phase 3: User Interface (Week 3)
- [ ] Create cost configuration widget
- [ ] Implement workload timeline visualization
- [ ] Add cost breakdown charts

### Phase 4: Analysis Tools (Week 4)
- [ ] Cost-effectiveness calculations
- [ ] Comparative analysis functions
- [ ] Export functionality for economic modeling

## 7. Validation and Testing

### 7.1 Cost Validation
- Compare total costs with NHS cost calculator outputs
- Validate injection frequencies match expected patterns
- Check workload metrics are realistic

### 7.2 Scenario Testing
1. **Biosimilar adoption**: Reduce Eylea cost to £355
2. **High-volume clinic**: Test with 1000+ patients
3. **Resource constraints**: Model impact of limited decision-makers

## 8. Future Enhancements

### 8.1 Advanced Features
- Multi-drug support with switching costs
- Virtual clinic modeling
- Capacity planning tools
- Budget impact over multiple years

### 8.2 Integration Opportunities
- Export to health economic models
- NICE submission format support
- Real-world data comparison tools

## 9. Key Design Decisions

### 9.1 Visit Type Determination
- **T&E**: Every visit is a full assessment (OCT + decision)
- **T&T**: Differentiate between injection-only and assessment visits
- **Loading phase**: Special handling for first/last visits

### 9.2 Workload Counting
- **Injection workload**: Count each injection administration
- **Decision workload**: Count visits requiring clinical judgment
- **Peak tracking**: Monitor maximum monthly workload

### 9.3 Cost Flexibility
- Allow override of any cost parameter
- Support for regional variations
- Easy switching between cost models

## 10. Success Criteria

1. **Accurate cost tracking**: Within 5% of manual calculations
2. **Clear visualization**: Stakeholders can easily understand cost drivers
3. **Flexible configuration**: Supports multiple NHS scenarios
4. **Performance**: No noticeable slowdown with cost tracking enabled
5. **Clinical relevance**: Outputs useful for service planning