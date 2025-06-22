# Cost Tracking Feature Summary

## Executive Summary
This feature adds comprehensive cost tracking and workload analysis to the VEGF simulation, enabling economic evaluation of different treatment protocols (T&E vs T&T) and resource planning for AMD services.

## Key Features

### 1. Flexible Cost Configuration
- **Drug costs**: Adjustable via slider (default £800 for Eylea 2mg)
- **Visit costs**: Based on NHS reference costs with component breakdown
- **Cost models**: NHS Standard 2025, Custom, or Minimal configurations

### 2. Visit Type Classification
The system distinguishes between:
- **Full Assessment Visits** (T&E): OCT + clinical decision + injection
- **Injection-Only Visits** (T&T): Nurse-led injection administration
- **Monitoring Visits**: Assessment without injection

### 3. Workload Tracking
Two key metrics tracked over time:
- **Injection workload**: Number of injections administered
- **Decision-maker workload**: Visits requiring consultant/clinical decisions

### 4. Cost-Effectiveness Analysis
- Total cost per patient over treatment period
- Cost per vision year saved
- Cost per patient maintaining driving vision
- Budget impact for different cohort sizes

## Implementation Approach

### Phase 1: Core Infrastructure
1. Enhance existing cost tracking classes
2. Add visit type classification logic
3. Create workload tracking system

### Phase 2: Protocol Integration
1. Modify protocols to determine visit types
2. Implement T&E vs T&T visit patterns
3. Add special handling for loading phase

### Phase 3: User Interface
1. Cost configuration sidebar widget
2. Workload timeline visualization
3. Cost breakdown charts
4. Protocol comparison displays

### Phase 4: Analysis & Reporting
1. Cost-effectiveness calculations
2. Export functionality
3. NICE-compatible reporting

## Key Differentiators

### T&E Protocol Characteristics
- Every visit includes full assessment (OCT + decision)
- Higher decision-maker workload
- Potentially fewer total visits
- More expensive per visit, but may be cheaper overall

### T&T Protocol Characteristics
- Most visits are injection-only (nurse-led)
- Quarterly safety assessments
- Lower decision-maker workload
- Cheaper per visit, but fixed schedule may mean more visits

## Expected Outputs

### 1. Visualizations
- **Workload Timeline**: Stacked area chart showing injections and assessments
- **Cost Breakdown**: Pie chart of drug vs procedure costs
- **Resource Heatmap**: Monthly utilization patterns
- **Comparison Dashboard**: Side-by-side T&E vs T&T metrics

### 2. Key Metrics
- Total cost: £1.2-1.4M for 300 patients over 5 years
- Cost per patient: £8,750 (T&E) vs £10,200 (T&T)
- Workload: ~250 procedures/month initially, declining over time
- Cost per vision year saved: £14,800-15,200

### 3. Export Options
- Patient-level cost data (CSV)
- Visit-level details (CSV)  
- Summary reports (JSON/PDF)
- NICE submission format

## Technical Considerations

### Performance
- Real-time cost calculation during simulation
- Efficient aggregation for large cohorts
- Responsive visualizations up to 10,000 patients

### Flexibility
- Easy addition of new drugs
- Configurable cost models
- Regional variation support

### Integration
- Works with existing simulation engines
- Compatible with both time-based and visit-based models
- Preserves all existing functionality

## Success Metrics

1. **Accuracy**: Costs within 5% of NHS calculator
2. **Usability**: Clinicians can configure and interpret without training
3. **Performance**: No noticeable slowdown vs non-cost simulations
4. **Value**: Outputs directly usable for service planning and commissioning

## Next Steps

1. Review and approve design documents
2. Begin Phase 1 implementation
3. Create test scenarios based on NHS cost calculator
4. Develop validation framework
5. Plan user testing with clinical teams

## Related Documents

1. `COST_TRACKING_IMPLEMENTATION_PLAN.md` - Detailed implementation plan
2. `COST_TRACKING_TECHNICAL_DESIGN.md` - Technical architecture
3. `COST_TRACKING_VISUALIZATION_DESIGN.md` - UI/UX specifications
4. `COST_TRACKING_DATA_REQUIREMENTS.md` - Data model and requirements